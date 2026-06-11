// Copyright 2026 etzhayyim Japan株式会社 / amanomibashira.
// Licensed under the Apache License, Version 2.0.

package provider

import (
	"context"
	"errors"
	"io"

	dto "github.com/prometheus/client_model/go"
	"github.com/virtual-kubelet/virtual-kubelet/node/api"
	statsv1alpha1 "k8s.io/kubelet/pkg/apis/stats/v1alpha1"
)

// The methods below complete the nodeutil.Provider surface. Murakumo's
// REST API does not expose container-level log streaming, exec/attach,
// kubelet stats summary, or port-forwarding, so these are intentionally
// no-op or unsupported. The README enumerates these as non-goals.

// GetContainerLogs — TODO: wire up murakumoctl-style log fetch when API
// support exists. Currently returns an empty stream with a hint.
func (p *Provider) GetContainerLogs(
	ctx context.Context, namespace, podName, containerName string, opts api.ContainerLogOpts,
) (io.ReadCloser, error) {
	return io.NopCloser(stringReader(
		"# murakumo-kubelet does not stream container logs via kubectl logs.\n" +
			"# Inspect the pod directly on Murakumo UI or via murakumoctl.\n",
	)), nil
}

// RunInContainer — exec is not bridged; use Murakumo SSH directly.
func (p *Provider) RunInContainer(
	ctx context.Context, namespace, podName, containerName string, cmd []string, attach api.AttachIO,
) error {
	return errors.New("RunInContainer not supported: use Murakumo SSH / web terminal")
}

// AttachToContainer — same as RunInContainer.
func (p *Provider) AttachToContainer(
	ctx context.Context, namespace, podName, containerName string, attach api.AttachIO,
) error {
	return errors.New("AttachToContainer not supported")
}

// PortForward — use Murakumo port mappings + the public URL printed in
// pod annotations instead.
func (p *Provider) PortForward(
	ctx context.Context, namespace, pod string, port int32, stream io.ReadWriteCloser,
) error {
	return errors.New("PortForward not supported: use Murakumo ports/HTTP proxy")
}

// GetStatsSummary returns an empty kubelet stats summary. Murakumo has
// per-pod billing metrics but doesn't expose the kubelet stats shape.
func (p *Provider) GetStatsSummary(ctx context.Context) (*statsv1alpha1.Summary, error) {
	return &statsv1alpha1.Summary{}, nil
}

// GetMetricsResource returns an empty metric family list.
func (p *Provider) GetMetricsResource(ctx context.Context) ([]*dto.MetricFamily, error) {
	return nil, nil
}

// ─── tiny helper: avoid pulling strings package just for one Reader ──

type stringReader string

func (s stringReader) Read(p []byte) (int, error) {
	if len(s) == 0 {
		return 0, io.EOF
	}
	n := copy(p, []byte(s))
	return n, nil
}
