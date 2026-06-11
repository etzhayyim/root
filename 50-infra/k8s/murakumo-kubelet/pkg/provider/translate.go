// Copyright 2026 etzhayyim Japan株式会社 / amanomibashira.
// Licensed under the Apache License, Version 2.0.

package provider

import (
	"fmt"
	"strconv"
	"strings"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"

	"github.com/etzhayyim/root/50-infra/k8s/murakumo-kubelet/pkg/murakumo"
)

// Annotation keys read off the k8s Pod spec.
//
// These let the workload author pick GPU type, cloud tier, ports, etc.
// without needing a CRD. Annotations are namespaced under
// `murakumo.etzhayyim.com/` so they don't collide with other tooling.
const (
	AnnoGPUType         = "murakumo.etzhayyim.com/gpu-type"           // e.g. "NVIDIA RTX A4000"; multiple = comma-separated
	AnnoGPUCount        = "murakumo.etzhayyim.com/gpu-count"          // int, default 1
	AnnoCloudType       = "murakumo.etzhayyim.com/cloud-type"         // "SECURE" | "COMMUNITY"
	AnnoVolumeMountPath = "murakumo.etzhayyim.com/volume-mount-path"  // default /workspace
	AnnoVolumeInGB      = "murakumo.etzhayyim.com/volume-gb"          // ephemeral data volume size
	AnnoNetworkVolume   = "murakumo.etzhayyim.com/network-volume-id"  // existing Murakumo network volume id
	AnnoContainerDisk   = "murakumo.etzhayyim.com/container-disk-gb"  // root disk size; default 20
	AnnoPorts           = "murakumo.etzhayyim.com/ports"              // "8188/http,22/tcp" → forwards to Murakumo's port format
	AnnoSupportPublicIP = "murakumo.etzhayyim.com/support-public-ip"  // "true"|"false"
	AnnoDataCenters     = "murakumo.etzhayyim.com/data-centers"       // comma-separated
	AnnoCountries       = "murakumo.etzhayyim.com/country-codes"      // comma-separated
)

// Translate converts a k8s Pod (with a single primary container) into a
// murakumo.PodCreate. We map the first non-init container's image/env/command
// onto the Murakumo pod; sidecars are not supported (Murakumo = 1 container/pod).
func Translate(pod *corev1.Pod, defaultGPUType, cloudType string) (*murakumo.PodCreate, error) {
	if len(pod.Spec.Containers) == 0 {
		return nil, fmt.Errorf("pod %s/%s has no containers", pod.Namespace, pod.Name)
	}
	if len(pod.Spec.Containers) > 1 {
		// Allowed; sidecars are silently dropped. Caller should consolidate.
		// Log/warn responsibility is in the provider, not here.
	}
	c := &pod.Spec.Containers[0]

	gpuType := annotation(pod, AnnoGPUType, defaultGPUType)
	gpuTypes := splitCSV(gpuType)
	gpuCount := annotationInt(pod, AnnoGPUCount, 1)
	
	// Check for GPU resource requests across all containers
	totalGPURequests := 0
	for _, container := range pod.Spec.Containers {
		if v, ok := container.Resources.Requests[corev1.ResourceName("nvidia.com/gpu")]; ok {
			if n, ok := v.AsInt64(); ok && n > 0 {
				totalGPURequests += int(n)
			}
		}
		if v, ok := container.Resources.Limits[corev1.ResourceName("nvidia.com/gpu")]; ok {
			if n, ok := v.AsInt64(); ok && n > 0 {
				totalGPURequests = max(totalGPURequests, int(n))
			}
		}
	}
	
	if totalGPURequests > 0 {
		gpuCount = totalGPURequests
	}

	// Note: Murakumo REST auto-allocates vCPU/RAM from GPU SKU; we don't
	// pass `containerCPU(c)` / `containerMemGB(c)` here. See PodCreate
	// docs in pkg/murakumo/client.go.
	envMap := map[string]string{}
	for _, e := range c.Env {
		if e.Value != "" {
			envMap[e.Name] = e.Value
		}
	}

	ports := splitCSV(annotation(pod, AnnoPorts, defaultPortsFromContainer(c)))

	out := &murakumo.PodCreate{
		Name:              fmt.Sprintf("k8s-%s-%s", pod.Namespace, pod.Name),
		ImageName:         c.Image,
		GPUTypeIDs:        gpuTypes,
		GPUCount:          gpuCount,
		ContainerDiskInGB: annotationInt(pod, AnnoContainerDisk, 20),
		VolumeInGB:        annotationInt(pod, AnnoVolumeInGB, 0),
		VolumeMountPath:   annotation(pod, AnnoVolumeMountPath, "/workspace"),
		NetworkVolumeID:   annotation(pod, AnnoNetworkVolume, ""),
		Ports:             ports,
		Env:               envMap,
		CloudType:         strings.ToUpper(annotation(pod, AnnoCloudType, cloudType)),
		DataCenterIDs:     splitCSV(annotation(pod, AnnoDataCenters, "")),
		CountryCodes:      splitCSV(annotation(pod, AnnoCountries, "")),
		SupportPublicIP:   annotationBool(pod, AnnoSupportPublicIP, true),
	}
	if len(c.Command) > 0 {
		out.DockerEntrypoint = c.Command
	}
	if len(c.Args) > 0 {
		out.DockerStartCmd = c.Args
	}
	return out, nil
}

// ───────────────────────── helpers ─────────────────────────────────

func annotation(pod *corev1.Pod, key, fallback string) string {
	if v, ok := pod.Annotations[key]; ok && v != "" {
		return v
	}
	return fallback
}

func annotationInt(pod *corev1.Pod, key string, fallback int) int {
	if v, ok := pod.Annotations[key]; ok {
		if n, err := strconv.Atoi(v); err == nil {
			return n
		}
	}
	return fallback
}

func annotationBool(pod *corev1.Pod, key string, fallback bool) bool {
	if v, ok := pod.Annotations[key]; ok {
		b, err := strconv.ParseBool(v)
		if err == nil {
			return b
		}
	}
	return fallback
}

func splitCSV(s string) []string {
	if s == "" {
		return nil
	}
	parts := strings.Split(s, ",")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		if p = strings.TrimSpace(p); p != "" {
			out = append(out, p)
		}
	}
	return out
}

func containerCPU(c *corev1.Container) int {
	for _, src := range []corev1.ResourceList{c.Resources.Limits, c.Resources.Requests} {
		if q, ok := src[corev1.ResourceCPU]; ok {
			// Murakumo expects whole vCPUs; round up.
			return int(qCeil(q))
		}
	}
	return 0
}

func containerMemGB(c *corev1.Container) int {
	for _, src := range []corev1.ResourceList{c.Resources.Limits, c.Resources.Requests} {
		if q, ok := src[corev1.ResourceMemory]; ok {
			bytes := q.Value()
			gb := bytes / (1024 * 1024 * 1024)
			if bytes%(1024*1024*1024) != 0 {
				gb++
			}
			return int(gb)
		}
	}
	return 0
}

// qCeil rounds a Quantity up to the next whole core. A request of 500m
// (half a core) still consumes one Murakumo vCPU.
func qCeil(q resource.Quantity) int64 {
	v := q.MilliValue()
	if v == 0 {
		return 0
	}
	whole := v / 1000
	if v%1000 != 0 {
		whole++
	}
	return whole
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func defaultPortsFromContainer(c *corev1.Container) string {
	if len(c.Ports) == 0 {
		return ""
	}
	parts := make([]string, 0, len(c.Ports))
	for _, p := range c.Ports {
		proto := "tcp"
		if strings.EqualFold(string(p.Protocol), "UDP") {
			proto = "udp"
		}
		// Murakumo's `8188/http` maps the container port to a public HTTP proxy.
		// We assume any HTTP-able exposed port wants the http proxy unless
		// the protocol says otherwise.
		if proto == "tcp" && p.ContainerPort != 22 {
			parts = append(parts, fmt.Sprintf("%d/http", p.ContainerPort))
		} else {
			parts = append(parts, fmt.Sprintf("%d/%s", p.ContainerPort, proto))
		}
	}
	return strings.Join(parts, ",")
}
