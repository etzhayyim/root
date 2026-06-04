# lg-ameno

K3s manifests for the Path-B ameno headless daemon
(`pymagatama.projects.ameno`).

This is the **production / fleet** deploy target for the Python ameno
daemon. Single-host dev still uses systemd (`ameno-daemon.service`) or
the TS Path A (`@etzhayyim/ameno-daemon`); this directory is for the
K3s-on-Murakumo path.

ADRs:
- [`90-docs/adr/2605191257-ameno-daemon-path-b-pymagatama-python.md`](../../../90-docs/adr/2605191257-ameno-daemon-path-b-pymagatama-python.md) — the code
- [`90-docs/adr/2605191346-etzhayyim-vultr-free-murakumo-control-plane.md`](../../../90-docs/adr/2605191346-etzhayyim-vultr-free-murakumo-control-plane.md) — why K3s on Mac-mini

## Files

| file | role |
|---|---|
| `Dockerfile` | Build context = repo root. Bundles `pymagatama` + uvicorn + langgraph. Runs `uvicorn pymagatama.projects.ameno.server:app`. |
| `deployment.yaml` | Namespace (`etzhayyim-langserver`) + ServiceAccount + PVC + Deployment + Service. |
| `kustomization.yaml` | Kustomize entry, pins the image tag. |

## Boundaries

- **Namespace**: `etzhayyim-langserver`. Distinct from `mitama-udf`
  (the etzhayyim.com legacy namespace) so the etzhayyim / etzhayyim split per
  ADR-2605191346 §2 is reflected at the cluster boundary.
- **nodeSelector**: `etzhayyim.com/role=murakumo-host`. Bind to Mac-mini
  fleet nodes (physical or via murakumo-kubelet virtual nodes).
- **No Vultr / EKS / GKE references.** Manifests in this directory MUST
  remain commercial-cloud-free.

## Build the image

```sh
# from the repo root
docker build \
  -f 50-infra/k8s/lg-ameno/Dockerfile \
  -t ghcr.io/etzhayyim/lg-ameno:$(git rev-parse --short HEAD) \
  .

docker push ghcr.io/etzhayyim/lg-ameno:$(git rev-parse --short HEAD)
```

## Deploy (dry-run cluster from `lima-k3s`)

```sh
# 1. point kubectl at the dry-run cluster
export KUBECONFIG=$(realpath ../lima-k3s/kubeconfig)

# 2. (one-time) label the VM that should host ameno
kubectl label node k3s-server-01 etzhayyim.com/role=murakumo-host --overwrite

# 3. apply
kubectl apply -k .

# 4. wait
kubectl -n etzhayyim-langserver rollout status deploy/lg-ameno
```

## Smoke test

```sh
# from inside the cluster network
kubectl -n etzhayyim-langserver port-forward svc/lg-ameno 12481:8080 &

curl http://127.0.0.1:12481/healthz
curl http://127.0.0.1:12481/workerInfo
# expect: {"did":"did:web:host:<…>","ollamaReachable":<true|false>,…}
```

If `ollamaReachable=false` either:
- the Ollama Service (`ollama.etzhayyim-langserver.svc.cluster.local:11434`)
  isn't deployed yet — follow-up to add `50-infra/k8s/ollama-fleet/`, or
- override at deploy time: `kubectl set env deploy/lg-ameno
  LOCAL_LLM_ENDPOINT=http://<your-ollama-host>:11434/api/chat`

## Topology vs lg-uhl-right-neural

| concern | lg-uhl-right-neural | lg-ameno (this) |
|---|---|---|
| pod containers | 2 (server + checkpointer sidecar) | 1 (server only) |
| checkpointer | MstCheckpointSaver (`@etzhayyim/sdk/checkpointer`) | FileCheckpointer (`pymagatama.projects.ameno.file_checkpointer`) |
| state volume | sidecar PVC `lg-uhl-right-neural-checkpointer-state` | server PVC `lg-ameno-state` |
| LLM driver | Anthropic (`langgraph dev`-managed) | Ollama (local fleet, `pymagatama.local_llm`) |
| namespace | `mitama-udf` (etzhayyim legacy) | `etzhayyim-langserver` (etzhayyim Murakumo) |

These differences are intentional. v0.1 of lg-ameno mirrors the
single-container Path A / Path B daemons so the FileCheckpointer code
path is exercised in K3s exactly as it is on launchd / systemd. A
follow-up PR will introduce the MstCheckpointSaver sidecar (same
ADR-2605171800 shape) and the migration is then a single env-var
flip + sidecar add — Path A and Path B daemons get the same
upgrade simultaneously.

## TODO (follow-up PRs)

1. `50-infra/k8s/ollama-fleet/` — Service + DaemonSet that fronts an
   Ollama instance on every Murakumo Mac-mini node.
2. MstCheckpointSaver sidecar (`@etzhayyim/sdk/checkpointer`) once the
   SDK ships — flip the deployment to the 2-container topology and
   delete the FileCheckpointer code path.
3. Memory-vault PVC layout — when Path B picks up ADR-2605191206
   (long-term encrypted memory vault), the same PVC already mounted
   at `/var/etzhayyim/ameno` can host the SQLite database with no
   schema migration.
4. Ingress — cloudflared sidecar or `traefik` IngressRoute publishing
   `ameno-daemon.etzhayyim.com` once the K3s cluster has a stable
   ingress story.

## License

Apache-2.0.
