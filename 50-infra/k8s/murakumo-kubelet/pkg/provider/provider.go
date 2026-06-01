// Copyright 2026 etzhayyim Japan株式会社 / amanomibashira.
// Licensed under the Apache License, Version 2.0.

// Package provider implements virtual-kubelet's PodLifecycleHandler +
// NodeProvider against Murakumo's REST API. Pods scheduled onto the
// virtual node `murakumo-vk` are translated into Murakumo pod create
// requests; status is reflected back into the k8s pod by polling.
//
// 1 k8s pod ↔ 1 Murakumo pod. Sidecars are not supported.
// PVCs are not bridged; use the Murakumo NetworkVolume annotation instead.
package provider

import (
	"context"
	"fmt"
	"strings"
	"sync"
	"time"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	"k8s.io/client-go/kubernetes"

	"github.com/etzhayyim/root/50-infra/k8s/murakumo-kubelet/pkg/config"
	"github.com/etzhayyim/root/50-infra/k8s/murakumo-kubelet/pkg/murakumo"
)

// AnnoMurakumoID is set by the provider on the k8s pod once the Murakumo
// pod has been created. Used to recover state on restart.
const AnnoMurakumoID = "murakumo.etzhayyim.com/pod-id"

// AnnoOptIn is the **mandatory** opt-in annotation. Without it the
// provider refuses to create a Murakumo pod. This is the cost-safety
// gate that prevents DaemonSet pods (calico-node, csi, prometheus
// node-exporter, etc.) from being silently shipped to Murakumo and
// incurring GPU charges. DaemonSets typically use
// `tolerations: [{ operator: Exists }]` which matches any taint on
// the virtual node, so we can NOT block them with taints alone.
//
// Workload authors set this explicitly:
//   metadata:
//     annotations:
//       murakumo.etzhayyim.com/route: "true"
const AnnoOptIn = "murakumo.etzhayyim.com/route"

// Provider is the virtual-kubelet PodLifecycleHandler + NodeProvider.
type Provider struct {
	cfg       *config.Config
	rp        *murakumo.Client
	k8s       kubernetes.Interface
	nodeName  string

	mu       sync.RWMutex
	tracked  map[string]*trackedPod // key = namespace/name
}

type trackedPod struct {
	k8sPod    *corev1.Pod
	murakumoID  string
	lastSync  time.Time
}

// New constructs a Provider.
func New(cfg *config.Config, rp *murakumo.Client, k8s kubernetes.Interface) *Provider {
	return &Provider{
		cfg:      cfg,
		rp:       rp,
		k8s:      k8s,
		nodeName: cfg.NodeName,
		tracked:  map[string]*trackedPod{},
	}
}

func podKey(ns, name string) string { return ns + "/" + name }

// ───────────────────── PodLifecycleHandler ─────────────────────────

// CreatePod is invoked when a pod is bound to our virtual node.
func (p *Provider) CreatePod(ctx context.Context, pod *corev1.Pod) error {
	// COST-SAFETY GATE — see AnnoOptIn docs. Without explicit opt-in,
	// we accept the pod silently but never spawn anything on Murakumo.
	// This blocks DaemonSet pods (calico, csi-node, node-exporter)
	// that tolerate any taint via `operator: Exists`.
	if pod.Annotations[AnnoOptIn] != "true" {
		p.mu.Lock()
		p.tracked[podKey(pod.Namespace, pod.Name)] = &trackedPod{
			k8sPod:   pod,
			murakumoID: "", // sentinel: skipped, never billed
			lastSync: time.Now(),
		}
		p.mu.Unlock()
		// Mark the pod Pending with a clear reason so operators see why.
		_ = p.patchSkippedPodStatus(ctx, pod)
		return nil
	}

	// If a Murakumo id is already on the pod (restart / reschedule), reuse it.
	if existing, ok := pod.Annotations[AnnoMurakumoID]; ok && existing != "" {
		p.mu.Lock()
		p.tracked[podKey(pod.Namespace, pod.Name)] = &trackedPod{k8sPod: pod, murakumoID: existing}
		p.mu.Unlock()
		return nil
	}

	req, err := Translate(pod, p.cfg.DefaultGPUType, p.cfg.OperatingMode)
	if err != nil {
		return fmt.Errorf("translate %s/%s: %w", pod.Namespace, pod.Name, err)
	}

	rpPod, err := p.rp.CreatePod(ctx, req)
	if err != nil {
		return fmt.Errorf("murakumo create: %w", err)
	}

	// Persist the Murakumo id on the k8s pod as an annotation.
	patch := []byte(fmt.Sprintf(
		`{"metadata":{"annotations":{%q:%q}}}`, AnnoMurakumoID, rpPod.ID,
	))
	if _, err := p.k8s.CoreV1().Pods(pod.Namespace).Patch(
		ctx, pod.Name, "application/strategic-merge-patch+json", patch, metav1.PatchOptions{},
	); err != nil {
		// Not fatal — the next reconcile will pick up the Murakumo pod by name.
		_ = err
	}

	p.mu.Lock()
	p.tracked[podKey(pod.Namespace, pod.Name)] = &trackedPod{
		k8sPod:   pod,
		murakumoID: rpPod.ID,
		lastSync: time.Now(),
	}
	p.mu.Unlock()
	return nil
}

// UpdatePod is mostly a no-op; Murakumo pods are immutable post-create.
// We accept the update but ignore image/env changes.
func (p *Provider) UpdatePod(ctx context.Context, pod *corev1.Pod) error {
	p.mu.Lock()
	if t, ok := p.tracked[podKey(pod.Namespace, pod.Name)]; ok {
		t.k8sPod = pod
	}
	p.mu.Unlock()
	return nil
}

// DeletePod terminates the corresponding Murakumo pod.
func (p *Provider) DeletePod(ctx context.Context, pod *corev1.Pod) error {
	id := pod.Annotations[AnnoMurakumoID]
	p.mu.Lock()
	if t, ok := p.tracked[podKey(pod.Namespace, pod.Name)]; ok {
		if id == "" {
			id = t.murakumoID
		}
		delete(p.tracked, podKey(pod.Namespace, pod.Name))
	}
	p.mu.Unlock()
	if id == "" {
		return nil // nothing to clean up
	}
	if err := p.rp.DeletePod(ctx, id); err != nil {
		return fmt.Errorf("murakumo delete %s: %w", id, err)
	}
	return nil
}

// GetPod returns the cached pod (status filled by reconcile loop).
func (p *Provider) GetPod(ctx context.Context, namespace, name string) (*corev1.Pod, error) {
	p.mu.RLock()
	t, ok := p.tracked[podKey(namespace, name)]
	p.mu.RUnlock()
	if !ok {
		return nil, nil
	}
	return t.k8sPod, nil
}

// GetPodStatus returns the pod's current status.
func (p *Provider) GetPodStatus(ctx context.Context, namespace, name string) (*corev1.PodStatus, error) {
	pod, err := p.GetPod(ctx, namespace, name)
	if err != nil || pod == nil {
		return nil, err
	}
	return &pod.Status, nil
}

// GetPods returns all pods this provider is currently tracking.
func (p *Provider) GetPods(ctx context.Context) ([]*corev1.Pod, error) {
	p.mu.RLock()
	defer p.mu.RUnlock()
	out := make([]*corev1.Pod, 0, len(p.tracked))
	for _, t := range p.tracked {
		out = append(out, t.k8sPod)
	}
	return out, nil
}

// ───────────────────── reconcile / status sync ─────────────────────

// Sync runs one reconcile pass: for each tracked pod, fetch Murakumo state
// and translate it back into k8s pod conditions. Caller should run this
// every 10-30 s in a goroutine.
func (p *Provider) Sync(ctx context.Context) error {
	p.mu.RLock()
	keys := make([]string, 0, len(p.tracked))
	for k := range p.tracked {
		keys = append(keys, k)
	}
	p.mu.RUnlock()

	for _, k := range keys {
		p.mu.RLock()
		t := p.tracked[k]
		p.mu.RUnlock()
		if t == nil || t.murakumoID == "" {
			continue
		}
		rp, err := p.rp.GetPod(ctx, t.murakumoID)
		if err != nil {
			// Don't surface as failure; next pass will retry.
			continue
		}
		p.reconcileStatus(ctx, t, rp)
	}
	return nil
}

func (p *Provider) reconcileStatus(ctx context.Context, t *trackedPod, rp *murakumo.Pod) {
	phase := mapPhase(rp.DesiredStatus, rp.CurrentStatus)
	pod := t.k8sPod.DeepCopy()
	pod.Status.Phase = phase
	pod.Status.PodIP = rp.PublicIP
	now := metav1.Now()
	if pod.Status.StartTime == nil && phase == corev1.PodRunning {
		pod.Status.StartTime = &now
	}
	pod.Status.Conditions = []corev1.PodCondition{
		{Type: corev1.PodReady, Status: condStatus(phase == corev1.PodRunning), LastTransitionTime: now},
		{Type: corev1.PodScheduled, Status: corev1.ConditionTrue, LastTransitionTime: now},
		{Type: corev1.PodInitialized, Status: corev1.ConditionTrue, LastTransitionTime: now},
	}
	if pod.Status.ContainerStatuses == nil && len(pod.Spec.Containers) > 0 {
		cs := make([]corev1.ContainerStatus, 0, len(pod.Spec.Containers))
		for _, c := range pod.Spec.Containers {
			cs = append(cs, corev1.ContainerStatus{
				Name:         c.Name,
				Ready:        phase == corev1.PodRunning,
				Image:        c.Image,
				ContainerID:  "murakumo://" + rp.ID,
				RestartCount: 0,
			})
		}
		pod.Status.ContainerStatuses = cs
	}

	if _, err := p.k8s.CoreV1().Pods(pod.Namespace).UpdateStatus(ctx, pod, metav1.UpdateOptions{}); err == nil {
		p.mu.Lock()
		t.k8sPod = pod
		t.lastSync = time.Now()
		p.mu.Unlock()
	}
}

// patchSkippedPodStatus marks an opted-out pod as Pending with a clear
// reason. We DON'T set Failed because the DaemonSet controller would
// treat that as terminal and never retry; Pending lets the pod sit
// quietly with a visible reason in `kubectl describe`.
func (p *Provider) patchSkippedPodStatus(ctx context.Context, pod *corev1.Pod) error {
	patched := pod.DeepCopy()
	patched.Status.Phase = corev1.PodPending
	patched.Status.Reason = "RequiresOptIn"
	patched.Status.Message = "murakumo-kubelet: pod is missing annotation `" + AnnoOptIn +
		"=true`; refusing to spawn on Murakumo (cost-safety default)"
	_, err := p.k8s.CoreV1().Pods(pod.Namespace).UpdateStatus(ctx, patched, metav1.UpdateOptions{})
	return err
}

func mapPhase(desired, current string) corev1.PodPhase {
	if current == "" {
		current = desired
	}
	switch current {
	case "RUNNING":
		return corev1.PodRunning
	case "EXITED", "TERMINATED", "DEAD":
		return corev1.PodSucceeded
	case "CREATED", "ASSIGNED", "STARTING":
		return corev1.PodPending
	default:
		return corev1.PodUnknown
	}
}

func condStatus(b bool) corev1.ConditionStatus {
	if b {
		return corev1.ConditionTrue
	}
	return corev1.ConditionFalse
}

// ───────────────────── NodeProvider ────────────────────────────────

// ConfigureNode fills the virtual Node object that this kubelet advertises.
func (p *Provider) ConfigureNode(_ context.Context, node *corev1.Node) {
	if node.Labels == nil {
		node.Labels = map[string]string{}
	}
	node.Labels["type"] = "virtual-kubelet"
	node.Labels["kubernetes.io/hostname"] = p.nodeName
	node.Labels["kubernetes.io/os"] = "linux"
	node.Labels["kubernetes.io/arch"] = "amd64"
	node.Labels["alpha.service-controller.kubernetes.io/exclude-balancer"] = "true"
	node.Labels["node.kubernetes.io/exclude-from-external-load-balancers"] = "true"
	node.Labels["topology.kubernetes.io/zone"] = "murakumo"
	node.Labels["gpu-provider"] = "murakumo"
	node.Labels["accelerator"] = "nvidia-gpu"
	node.Labels["gpu.murakumo.ai/type"] = strings.ReplaceAll(p.cfg.DefaultGPUType, " ", "-")
	if p.cfg.Region != "" {
		node.Labels["topology.kubernetes.io/region"] = p.cfg.Region
	}
	if p.cfg.EnableGPUSharing {
		node.Labels["gpu.murakumo.ai/sharing"] = "enabled"
	}
	for k, v := range p.cfg.NodeLabels {
		node.Labels[k] = v
	}

	// Dynamic capacity based on config and GPU type
	gpuCount := "16"
	if p.cfg.MaxGPUsPerPod > 0 {
		gpuCount = fmt.Sprintf("%d", p.cfg.MaxGPUsPerPod)
	}
	
	node.Status.Capacity = corev1.ResourceList{
		corev1.ResourceCPU:                       resource.MustParse("96"),
		corev1.ResourceMemory:                    resource.MustParse("480Gi"),
		corev1.ResourcePods:                      resource.MustParse("100"),
		corev1.ResourceName("nvidia.com/gpu"):    resource.MustParse(gpuCount),
	}
	
	// Add GPU memory resource if configured
	if p.cfg.GPUMemoryGB > 0 {
		gpuMemory := fmt.Sprintf("%dGi", p.cfg.GPUMemoryGB*16) // 16 GPUs worth
		node.Status.Capacity[corev1.ResourceName("nvidia.com/gpu-memory")] = resource.MustParse(gpuMemory)
	}
	node.Status.Allocatable = node.Status.Capacity.DeepCopy()
	node.Status.Conditions = nodeReadyConditions()
	node.Status.NodeInfo.OperatingSystem = "linux"
	node.Status.NodeInfo.Architecture = "amd64"
	node.Status.NodeInfo.KubeletVersion = "v1.30.0-murakumo-vk"

	// Add a taint so pods only land here on explicit toleration.
	node.Spec.Taints = []corev1.Taint{{
		Key:    "murakumo.etzhayyim.com/virtual-kubelet",
		Value:  "true",
		Effect: corev1.TaintEffectNoSchedule,
	}}
}

// Ping is used by the virtual-kubelet SDK as a liveness probe.
func (p *Provider) Ping(ctx context.Context) error { return nil }

// NotifyNodeStatus is called by virtual-kubelet to subscribe to node
// status updates. We provide a periodic Ready heartbeat.
func (p *Provider) NotifyNodeStatus(ctx context.Context, cb func(*corev1.Node)) {
	go func() {
		t := time.NewTicker(30 * time.Second)
		defer t.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-t.C:
				n := &corev1.Node{
					ObjectMeta: metav1.ObjectMeta{Name: p.nodeName},
				}
				p.ConfigureNode(ctx, n)
				cb(n)
			}
		}
	}()
}

func nodeReadyConditions() []corev1.NodeCondition {
	now := metav1.Now()
	return []corev1.NodeCondition{
		{Type: corev1.NodeReady, Status: corev1.ConditionTrue, LastHeartbeatTime: now, LastTransitionTime: now,
			Reason: "KubeletReady", Message: "murakumo-vk reachable"},
		{Type: corev1.NodeMemoryPressure, Status: corev1.ConditionFalse, LastHeartbeatTime: now, LastTransitionTime: now,
			Reason: "MurakumoHasSufficientMemory"},
		{Type: corev1.NodeDiskPressure, Status: corev1.ConditionFalse, LastHeartbeatTime: now, LastTransitionTime: now,
			Reason: "MurakumoHasNoDiskPressure"},
		{Type: corev1.NodePIDPressure, Status: corev1.ConditionFalse, LastHeartbeatTime: now, LastTransitionTime: now,
			Reason: "MurakumoHasSufficientPID"},
		{Type: corev1.NodeNetworkUnavailable, Status: corev1.ConditionFalse, LastHeartbeatTime: now, LastTransitionTime: now,
			Reason: "RouteCreated"},
	}
}
