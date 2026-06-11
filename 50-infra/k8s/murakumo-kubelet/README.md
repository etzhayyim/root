# murakumo-kubelet

Virtual-kubelet for Murakumo. Schedules Kubernetes pods onto Murakumo via
the public REST API, presenting Murakumo as a virtual node
(`murakumo-vk` by default) on your existing k8s cluster. Apache 2.0.

Built under the etzhayyim open religious-corp scope because the (sole existing) OSS
implementation (`BSVogler/k8s-murakumo-kubelet`) is non-commercial-licensed
+ DRM-gated behind GPU Conduit. ADR 2605110100 in vendor monorepo.

## Why

You already have a VKE / EKS / GKE cluster running CPU workloads
(Kotoba/Datomic, control plane, ingest workers, …). You need bursty GPU
capacity for SDXL inference or LLM serving but don't want to:

- pay for 24×7 dedicated GPU you don't fully use
- manage a second Kubernetes cluster on a GPU cloud
- write your own Murakumo REST glue inside every workload

`murakumo-kubelet` lets you `kubectl apply` a normal Pod with a
`murakumo.etzhayyim.com/virtual-kubelet:NoSchedule` toleration; the pod gets
spawned on Murakumo and appears in `kubectl get pod` with the
`murakumo-vk` node. Delete the k8s pod → the Murakumo pod terminates.

## How it maps

| k8s pod field | Murakumo equivalent |
|---|---|
| `spec.containers[0].image` | `imageName` |
| `spec.containers[0].command` / `args` | `dockerEntrypoint` / `dockerStartCmd` |
| `spec.containers[0].env` (literal values only) | `env` |
| `spec.containers[0].resources.limits[nvidia.com/gpu]` | `gpuCount` |
| `spec.containers[0].resources.requests.cpu` (ceil) | `vcpuCount` |
| `spec.containers[0].resources.requests.memory` (GiB, ceil) | `memoryInGb` |
| `spec.containers[0].ports[]` | `ports` (HTTP-proxied) |
| annotation `murakumo.etzhayyim.com/gpu-type` | `gpuTypeIds` (CSV) |
| annotation `murakumo.etzhayyim.com/cloud-type` | `cloudType` (SECURE / COMMUNITY) |
| annotation `murakumo.etzhayyim.com/network-volume-id` | `networkVolumeId` (existing volume id) |
| annotation `murakumo.etzhayyim.com/volume-mount-path` | `volumeMountPath` (default `/workspace`) |
| annotation `murakumo.etzhayyim.com/data-centers` | `dataCenterIds` (CSV) |
| annotation `murakumo.etzhayyim.com/country-codes` | `countryCodes` (CSV) |
| annotation `murakumo.etzhayyim.com/support-public-ip` | `supportPublicIp` (bool) |

PVCs are **not** bridged — Murakumo pods don't honor k8s `PersistentVolume`
semantics. Use a Murakumo `NetworkVolume` and reference it by id via
annotation.

## Install

```bash
# Murakumo API key (you have this already if you're using murakumoctl)
MURAKUMO_API_KEY=$(security find-generic-password -s etzhayyim.murakumo -a MURAKUMO_API_KEY -w)

# Build + push image (uses remote BuildKit; see 50-infra/k8s/buildkit/)
make image IMAGE=ghcr.io/etzhayyim/murakumo-kubelet TAG=v0.1.0

helm upgrade --install murakumo-kubelet \
  50-infra/k8s/murakumo-kubelet/helm/murakumo-kubelet/ \
  --namespace kube-system \
  --set image.tag=v0.1.0 \
  --set murakumo.apiKey="${MURAKUMO_API_KEY}" \
  --set defaultGpuType="NVIDIA RTX A4000"

kubectl get node murakumo-vk
# NAME        STATUS   ROLES   AGE   VERSION
# murakumo-vk   Ready    agent   12s   v1.30.0-murakumo-vk
```

## Schedule a pod onto Murakumo

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: comfyui-burst
  namespace: keiei-llm
  annotations:
    murakumo.etzhayyim.com/gpu-type: "NVIDIA RTX A4000"
    murakumo.etzhayyim.com/cloud-type: "SECURE"
    murakumo.etzhayyim.com/network-volume-id: "p9riuzhrvf"
    murakumo.etzhayyim.com/ports: "8188/http,22/tcp"
    murakumo.etzhayyim.com/container-disk-gb: "30"
spec:
  nodeSelector: { type: virtual-kubelet }
  tolerations:
    - key: murakumo.etzhayyim.com/virtual-kubelet
      operator: Equal
      value: "true"
      effect: NoSchedule
  containers:
    - name: comfyui
      image: ghcr.io/etzhayyim/comfyui:cu124
      ports: [{ containerPort: 8188 }]
      resources:
        limits: { nvidia.com/gpu: 1 }
```

Apply, watch:

```bash
kubectl apply -f comfyui-burst.yaml
kubectl describe pod -n keiei-llm comfyui-burst | tail
# Annotations:    murakumo.etzhayyim.com/pod-id: <MURAKUMO_POD_ID>
# Status:         Running
```

## How it works

```
┌──────────────────────────────────────────────────────────────────┐
│  Kubernetes API server                                           │
│                                                                  │
│    Pod ─────► scheduler ───► binds to node murakumo-vk             │
│                                              │                   │
│                                              ▼                   │
│    Node controller (this kubelet) ─── PodLifecycleHandler        │
│                                              │                   │
└──────────────────────────────────────────────┼───────────────────┘
                                               │
                            Murakumo REST API: POST /v1/pods
                                               │
                                               ▼
                                  ┌──────────────────────────┐
                                  │  Murakumo Cloud            │
                                  │                          │
                                  │  Pod = container running │
                                  │  the k8s pod's image     │
                                  │  with GPU attached       │
                                  └──────────────────────────┘
                                               ▲
                            polling reconcile (every --sync-interval, default 15s)
                                               │
                                               ▼
                                    GET /v1/pods/{id} → k8s pod status
```

The kubelet:
1. registers a virtual `Node` named `murakumo-vk` (taint
   `murakumo.etzhayyim.com/virtual-kubelet=true:NoSchedule` so only opted-in
   pods land there)
2. watches pods bound to that node and translates them via
   `pkg/provider/translate.go` → Murakumo `POST /v1/pods`
3. patches the k8s pod with the Murakumo pod id under
   `murakumo.etzhayyim.com/pod-id` for resilience across kubelet restarts
4. every `--sync-interval` polls each Murakumo pod and updates the
   matching k8s pod's `status.phase`, `status.podIP`,
   `status.containerStatuses[]`
5. on k8s pod deletion → `DELETE /v1/pods/{id}` to release Murakumo resources

## Limits + non-goals

- **One container per k8s pod.** Sidecars are dropped. Murakumo = 1
  container per pod by design. If you need a sidecar, run it on a
  regular k8s node.
- **No PVC bridging.** Use Murakumo `NetworkVolume` (mount via
  `murakumo.etzhayyim.com/network-volume-id`).
- **No exec into the pod via `kubectl exec`.** Use Murakumo's SSH or
  web terminal directly.
- **No log streaming via `kubectl logs`.** Use Murakumo's UI or REST.
- **No autoscaling** — this is a kubelet (provider), not a controller.
  Combine with HPA or external job dispatcher if you need scale-out.
- **No multi-cloud routing.** Just Murakumo. If you want
  Vast.ai/Lambda/etc on the same virtual node, that's GPU Conduit's
  territory.

## Roadmap

- [ ] kubectl logs via Murakumo's logs endpoint
- [ ] Metrics (pod count, Murakumo API latency, cost-per-hour) →
      Prometheus via DCGM-style annotations
- [ ] Spot / on-demand pricing knob (cheapest available match)
- [ ] Lifecycle: graceful stop vs hard delete
- [ ] Tests against a Murakumo sandbox account

## License

Apache 2.0. See `LICENSE`. This project does not include any code from
`BSVogler/k8s-murakumo-kubelet`; the REST endpoints used are Murakumo's
public API documented at <https://docs.murakumo.io/api-reference>.
