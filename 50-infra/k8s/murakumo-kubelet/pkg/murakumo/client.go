// Copyright 2026 etzhayyim Japan株式会社 / amanomibashira.
// Licensed under the Apache License, Version 2.0.

// Package murakumo is a thin client over the Murakumo public REST API
// (https://rest.murakumo.io/v1). Covers the subset of endpoints the
// virtual-kubelet provider needs: Create, Get, List, Stop, Delete pods.
//
// All request shapes are derived from the official Murakumo REST docs.
// No third-party Murakumo client code is used.
package murakumo

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

const (
	defaultBaseURL = "https://rest.murakumo.io/v1"
	defaultTimeout = 30 * time.Second
)

// Client is the Murakumo REST client.
type Client struct {
	apiKey  string
	baseURL string
	http    *http.Client
}

// New returns a Client. apiKey must be a non-empty Murakumo API key.
func New(apiKey string) *Client {
	return &Client{
		apiKey:  apiKey,
		baseURL: defaultBaseURL,
		http:    &http.Client{Timeout: defaultTimeout},
	}
}

// WithBaseURL overrides the API endpoint (useful for tests).
func (c *Client) WithBaseURL(u string) *Client { c.baseURL = u; return c }

// WithHTTP swaps the HTTP client.
func (c *Client) WithHTTP(h *http.Client) *Client { c.http = h; return c }

// ───────────────────────── pod data shapes ─────────────────────────

// PodCreate is the minimum-viable Murakumo pod create request body.
// Optional fields are omitted on zero-value; callers populate what they need.
//
// NOTE: Murakumo's REST API (rest.murakumo.io/v1) auto-allocates vCPU and
// RAM from the chosen GPU SKU. Older GraphQL-style fields like
// `vcpuCount` / `memoryInGb` are explicitly REJECTED with
// `Extra input keys provided in request body`. Do not add them back.
type PodCreate struct {
	Name              string            `json:"name"`
	ImageName         string            `json:"imageName"`
	GPUTypeIDs        []string          `json:"gpuTypeIds,omitempty"`        // e.g. ["NVIDIA RTX A4000"]
	GPUCount          int               `json:"gpuCount,omitempty"`
	ContainerDiskInGB int               `json:"containerDiskInGb,omitempty"`
	VolumeInGB        int               `json:"volumeInGb,omitempty"`
	VolumeMountPath   string            `json:"volumeMountPath,omitempty"`
	NetworkVolumeID   string            `json:"networkVolumeId,omitempty"`
	Ports             []string          `json:"ports,omitempty"` // e.g. ["8188/http","22/tcp"]
	Env               map[string]string `json:"env,omitempty"`
	CloudType         string            `json:"cloudType,omitempty"` // "SECURE" | "COMMUNITY"
	DataCenterIDs     []string          `json:"dataCenterIds,omitempty"`
	CountryCodes      []string          `json:"countryCodes,omitempty"`
	DockerStartCmd    []string          `json:"dockerStartCmd,omitempty"`
	DockerEntrypoint  []string          `json:"dockerEntrypoint,omitempty"`
	SupportPublicIP   bool              `json:"supportPublicIp,omitempty"`
	// GPU-specific fields for K8s integration
	GPUMemoryFraction float64           `json:"-"` // internal: fractional GPU allocation
	GPUDevicePlugin   bool              `json:"-"` // internal: enable device plugin mode
}

// Pod is the Murakumo pod resource as returned by the API.
type Pod struct {
	ID              string            `json:"id"`
	Name            string            `json:"name"`
	DesiredStatus   string            `json:"desiredStatus"` // RUNNING | EXITED | TERMINATED | etc.
	CurrentStatus   string            `json:"currentStatus,omitempty"`
	ImageName       string            `json:"imageName"`
	MachineID       string            `json:"machineId,omitempty"`
	DataCenterID    string            `json:"dataCenterId,omitempty"`
	PublicIP        string            `json:"publicIp,omitempty"`
	Ports           []string          `json:"ports,omitempty"`
	PortMappings    map[string]int    `json:"portMappings,omitempty"`
	CostPerHr       float64           `json:"costPerHr,omitempty"`
	CreatedAt       string            `json:"createdAt,omitempty"`
	LastStartedAt   string            `json:"lastStartedAt,omitempty"`
	Env             map[string]string `json:"env,omitempty"`
}

// ───────────────────────── HTTP plumbing ───────────────────────────

func (c *Client) do(ctx context.Context, method, path string, body, out interface{}) error {
	var rd io.Reader
	if body != nil {
		buf, err := json.Marshal(body)
		if err != nil {
			return fmt.Errorf("marshal: %w", err)
		}
		rd = bytes.NewReader(buf)
	}
	req, err := http.NewRequestWithContext(ctx, method, c.baseURL+path, rd)
	if err != nil {
		return fmt.Errorf("new request: %w", err)
	}
	req.Header.Set("Authorization", "Bearer "+c.apiKey)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	resp, err := c.http.Do(req)
	if err != nil {
		return fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)

	if resp.StatusCode >= 400 {
		return fmt.Errorf("murakumo %s %s → %d: %s", method, path, resp.StatusCode, string(respBody))
	}
	if out != nil && len(respBody) > 0 {
		if err := json.Unmarshal(respBody, out); err != nil {
			return fmt.Errorf("unmarshal: %w (body=%s)", err, string(respBody))
		}
	}
	return nil
}

// ───────────────────────── pod operations ──────────────────────────

// CreatePod creates a new Murakumo pod and returns its id + initial state.
func (c *Client) CreatePod(ctx context.Context, p *PodCreate) (*Pod, error) {
	var out Pod
	if err := c.do(ctx, http.MethodPost, "/pods", p, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// GetPod fetches the current state of a pod by id.
func (c *Client) GetPod(ctx context.Context, id string) (*Pod, error) {
	var out Pod
	if err := c.do(ctx, http.MethodGet, "/pods/"+id, nil, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

// ListPods returns all pods on the account.
func (c *Client) ListPods(ctx context.Context) ([]Pod, error) {
	var out struct {
		Pods []Pod `json:"pods"`
	}
	if err := c.do(ctx, http.MethodGet, "/pods", nil, &out); err != nil {
		return nil, err
	}
	return out.Pods, nil
}

// StopPod transitions a pod to EXITED but keeps it billable for restart.
// Use DeletePod to fully release resources.
func (c *Client) StopPod(ctx context.Context, id string) error {
	return c.do(ctx, http.MethodPost, "/pods/"+id+"/stop", nil, nil)
}

// DeletePod terminates and fully releases the pod.
func (c *Client) DeletePod(ctx context.Context, id string) error {
	return c.do(ctx, http.MethodDelete, "/pods/"+id, nil, nil)
}
