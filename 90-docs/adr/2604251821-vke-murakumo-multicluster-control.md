---
id: adr-2604251821-vke-murakumo-multicluster-control
title: "ADR: VKE hub + Murakumo k3s pull-mode multi-cluster control"
status: accepted
doc_type: adr
topic: vke-murakumo-multicluster-control
authoritative: true
last_verified: 2026-04-27
authoritative_for:
  - VKE and Murakumo k3s multi-cluster control topology
  - Murakumo Mac mini fleet registration without joining VKE as nodes
  - placement policy for yoro actor workers across VKE and Murakumo
  - pull-mode cluster control boundary for private LAN clusters
related:
  - adr-2604251758-murakumo-yoro-actor-worker-fleet
  - adr-2604250836-langgraph-as-zeebe-servicetask
  - adr-0056-bpmn-as-actor
  - adr-0048-kotoba-vultr-b2-primary
  - adr-0061-murakumo-platform-auth-unification
supersedes: []
superseded_by: []
---

# Context

Vultr Kubernetes Engine (VKE) is the managed cloud cluster that currently hosts
Kotoba/Datomic, Zeebe, mitama UDF workers, and other cloud-side services. Murakumo
is now an 11-node Mac mini k3s cluster that runs per-node llama.cpp Vulkan
inference and yoro/shinka actor workers.

The Mac mini nodes must **not** be attached to VKE as worker nodes. VKE node
pools are Vultr-managed infrastructure, and the Murakumo nodes live behind a
LAN/WireGuard boundary with different CNI, storage, node lifecycle, and GPU
semantics. Treating them as one Kubernetes node pool would blur failure domains
and create unsupported operations.

# Decision

Adopt **pull-mode multi-cluster control**:

- VKE is the hub/control cluster for policy, placement, and cloud services.
- Murakumo k3s is a member cluster, not a VKE node pool.
- Murakumo runs an outbound agent that pulls work from the hub. The hub does
  not require inbound access to the Murakumo API server.
- Workloads are placed by cluster labels and namespace ownership. No workload
  may fall back to the `default` namespace.

The selected control implementation is **Karmada pull mode** once the bootstrap
is applied. Until Karmada CRDs are installed, the repo stores the topology and
placement contracts as declarative bootstrap inputs under
`50-infra/multicluster/murakumo-vke/`.

## Cluster Roles

| Cluster | Role | Owns |
|---|---|---|
| `vke-primary` | hub + cloud services | `kotoba`, `mitama-udf`, `zeebe-system`, public ingress, long-lived cloud PVCs |
| `murakumo-k3s` | private GPU/actor worker member | `murakumo-system`, `yoro-actors`, per-node llama.cpp Vulkan, Mac-local actor workers |

## Placement Rules

| Workload class | Placement |
|---|---|
| Kotoba/Datomic / metastore / B2-backed DB | `vke-primary` |
| Zeebe broker/gateway | `vke-primary` initially; may move to `zeebe-system` on Murakumo only by new migration |
| bpmn-dispatcher | `vke-primary` |
| pyzeebe generic workers | `vke-primary` by default; actor-heavy workers can be propagated to Murakumo |
| yoro LangGraph agent workers | `murakumo-k3s` |
| llama.cpp Vulkan DaemonSet | `murakumo-k3s`, `murakumo-system/llama-vulkan-fleet` |
| MCP adapter for yoro actor tools | `murakumo-k3s`, with PDS dispatch still going through `atproto.etzhayyim.com` |
| public HTTP ingress | VKE / Cloudflare Worker; Murakumo exposes only explicit service endpoints |

## Network Boundary

Control plane:

- Murakumo member agent connects outbound to the VKE-hosted Karmada API.
- No VKE component depends on `https://127.0.0.1:26443` or
  `murakumo.orb.local`.
- Member kubeconfigs and tokens stay in Keychain or Kubernetes Secrets; they
  are never committed.

Data plane:

- VKE services call Murakumo services through an explicit gateway:
  WireGuard gateway, Cloudflare Tunnel, or a future service mesh endpoint.
- Cross-cluster Service DNS is not assumed. Use explicit URLs/env vars for
  cross-cluster calls.
- Pod CIDRs are not merged between clusters.

## Required Labels

Cluster labels:

```yaml
etzhayyim.com/cluster-role: hub | gpu-actor-worker
etzhayyim.com/location: vultr-lax | murakumo-lan
etzhayyim.com/gpu.apple-vulkan: "true" | "false"
etzhayyim.com/storage.cloud-pvc: "true" | "false"
```

Namespace ownership:

```yaml
etzhayyim.com/placement-owner: vke-primary | murakumo-k3s
etzhayyim.com/default-namespace-forbidden: "true"
```

# Consequences

Positive:

- Murakumo becomes schedulable as a cluster-level target without pretending to
  be a VKE node pool.
- VKE remains responsible for durable cloud services and public ingress.
- Murakumo can stay private and egress-only.
- Placement is explicit, auditable, and compatible with ADR-2604251758.

Trade-offs:

- Karmada introduces a new control-plane dependency and CRDs.
- Pull-mode registration requires bootstrap tokens and member agents.
- Cross-cluster service calls remain explicit; Kubernetes Service DNS is
  cluster-local.
- A full end-to-end rollout needs a later apply step on both clusters.

# Bootstrap Plan

1. Install Karmada control plane into VKE namespace `karmada-system`.
2. Expose Karmada API through a restricted endpoint reachable from Murakumo
   agents.
3. Register `vke-primary` as local member and `murakumo-k3s` as pull-mode
   member.
4. Apply cluster labels from
   `50-infra/multicluster/murakumo-vke/topology.yaml`.
5. Apply placement policies for:
   - `murakumo-system` and `yoro-actors` → `murakumo-k3s`
   - `kotoba`, `mitama-udf`, `zeebe-system` → `vke-primary`
6. Verify:
   - both clusters report Ready in the hub
   - no resource is created in `default`
   - `murakumo-system/llama-vulkan-fleet` reports all 11 Mac mini nodes Ready
   - compatibility Service `murakumo-system/llama-vulkan` selects the fleet
     DaemonSet endpoints
   - VKE bpmn-dispatcher can reach the selected Murakumo inference endpoint

# Verified State

As of 2026-04-27, the Murakumo member cluster runs
`murakumo-system/llama-vulkan-fleet` as a DaemonSet on all 11 Mac mini nodes.
The image is published as
`ghcr.io/etzhayyim/murakumo-llama-vulkan:20260427-fleet-arm64`, and both
`llama-vulkan-fleet` and compatibility Service `llama-vulkan` select the same
pod set. Service-local `/v1/models` returns `smollm2-vulkan`.

# Prohibitions

- Do not join Murakumo nodes to VKE as worker nodes.
- Do not expose the Murakumo kube-apiserver publicly for hub push-mode control.
- Do not merge pod CIDRs or assume cross-cluster Service DNS.
- Do not create fallback resources in `default`.
- Do not move Kotoba/Datomic storage to Murakumo Mac mini local disks.
