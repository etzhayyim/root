// Copyright 2026 etzhayyim Japan株式会社 / amanomibashira.
// Licensed under the Apache License, Version 2.0.

// Package config holds the kubelet's runtime configuration loaded from env.
package config

import (
	"fmt"
	"os"
	"strconv"
	"strings"
)

type Config struct {
	NodeName       string // virtual node name (default: murakumo-vk)
	APIKey         string // MURAKUMO_API_KEY
	APIURL         string // MURAKUMO_API_URL (optional override)
	KubeConfig     string // path; empty = in-cluster
	OperatingMode  string // "secure" | "community"
	DefaultGPUType string // fallback GPU id (e.g. "NVIDIA RTX A4000")
	Region         string // optional default region label
	NodeLabels     map[string]string
	GPUMemoryGB    int    // GPU memory in GB for resource allocation
	MaxGPUsPerPod  int    // maximum GPUs per pod
	EnableGPUSharing bool // allow fractional GPU allocation
}

// FromEnv reads config from environment variables.
func FromEnv() (*Config, error) {
	c := &Config{
		NodeName:       getenv("MURAKUMO_VK_NODE_NAME", "murakumo-vk"),
		APIKey:         os.Getenv("MURAKUMO_API_KEY"),
		APIURL:         os.Getenv("MURAKUMO_API_URL"),
		KubeConfig:     os.Getenv("KUBECONFIG"),
		OperatingMode:  strings.ToLower(getenv("MURAKUMO_CLOUD_TYPE", "secure")),
		DefaultGPUType: getenv("MURAKUMO_DEFAULT_GPU_TYPE", "NVIDIA RTX A4000"),
		Region:         os.Getenv("MURAKUMO_DEFAULT_REGION"),
		NodeLabels:     parseLabels(os.Getenv("MURAKUMO_VK_NODE_LABELS")),
		GPUMemoryGB:    parseInt(getenv("MURAKUMO_GPU_MEMORY_GB", "16")),
		MaxGPUsPerPod:  parseInt(getenv("MURAKUMO_MAX_GPUS_PER_POD", "8")),
		EnableGPUSharing: getenv("MURAKUMO_ENABLE_GPU_SHARING", "false") == "true",
	}
	if c.APIKey == "" {
		return nil, fmt.Errorf("MURAKUMO_API_KEY required")
	}
	switch c.OperatingMode {
	case "secure", "community":
		// ok
	default:
		return nil, fmt.Errorf("MURAKUMO_CLOUD_TYPE must be 'secure' or 'community', got %q", c.OperatingMode)
	}
	return c, nil
}

func getenv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func parseLabels(s string) map[string]string {
	out := map[string]string{}
	if s == "" {
		return out
	}
	for _, kv := range strings.Split(s, ",") {
		kv = strings.TrimSpace(kv)
		if i := strings.IndexByte(kv, '='); i > 0 {
			out[kv[:i]] = kv[i+1:]
		}
	}
	return out
}

func parseInt(s string) int {
	if v, err := strconv.Atoi(s); err == nil {
		return v
	}
	return 0
}
