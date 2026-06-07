---
id: lg-karute-readme
title: lg-karute — LangServer pod for karute Pregel
status: active
doc_type: how-to
topic: karute-langserver
authoritative: true
last_verified: 2026-05-23
related:
  - ../../../90-docs/adr/2605231100-karute-emr-phase1.md
  - ../../../90-docs/adr/2605231400-karute-consent-capability-iryo-bridge.md
  - ../../../90-docs/adr/2605231603-per-record-rekey-tombstone-protocol.md
  - ../../../90-docs/adr/2605231700-audit-webhook-subsystem.md
  - ../../../90-docs/adr/2605231900-karute-deployment-topology.md
---

# lg-karute

LangServer pod serving the `karute` 31-pipeline StateGraph
(`kotodama.projects.karute.pregel:app`) over the standard LangGraph
CLI HTTP runtime.

## Files

| File | Role |
|---|---|
| `Dockerfile` | python:3.11-slim + langgraph-cli + kotodama (editable install) |
| `langgraph.json` | LangGraph CLI config — registers `karute` graph |
| `deployment.yaml` | k8s ServiceAccount + PVC + Deployment + Service (2-container pod) |

## Build + push

```bash
# from repo root (build context is repo root so COPY can reach 20-actors/)
GIT_SHA=$(git rev-parse --short HEAD)
docker build \
  -f 50-infra/k8s/lg-karute/Dockerfile \
  -t ghcr.io/etzhayyim/lg-karute:$GIT_SHA \
  -t ghcr.io/etzhayyim/lg-karute:main \
  .
docker push ghcr.io/etzhayyim/lg-karute:$GIT_SHA
docker push ghcr.io/etzhayyim/lg-karute:main
```

## Deploy

```bash
# Namespace must exist (shared with other lg-* pods).
kubectl create namespace mitama-udf --dry-run=client -o yaml | kubectl apply -f -

# Image pull secret for ghcr.io
kubectl create secret docker-registry ghcr-pull \
  --namespace mitama-udf \
  --docker-server=ghcr.io \
  --docker-username=$GITHUB_USER \
  --docker-password=$GITHUB_PAT \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -f 50-infra/k8s/lg-karute/deployment.yaml

kubectl -n mitama-udf rollout status deploy/lg-karute --timeout=120s
kubectl -n mitama-udf get pods -l app.kubernetes.io/name=lg-karute
```

## Smoke test

```bash
# port-forward (one-shot)
kubectl -n mitama-udf port-forward svc/lg-karute 8080:8080 &

# Health probe (LangGraph CLI exposes /ok)
curl -fsS http://localhost:8080/ok

# Run a stub pipeline — listPatients via the karute graph
curl -fsS -X POST http://localhost:8080/invoke \
  -H 'content-type: application/json' \
  -d '{"graph":"karute","input":{"pipeline":"list_patients","input":{"limit":10}}}' | jq

# Expected: {"output":{"status":"stub","pipeline":"list_patients","note":"Phase 1 — substrate seams pending"}, ...}
```

## CF Tunnel (XRPC reach from karute.etzhayyim.com)

The DID Worker at `50-infra/karute-did-web/` reverse-proxies `/xrpc/*` to
the LangServer Pod. A CF Tunnel provides a stable public origin:

```bash
cloudflared tunnel create lg-karute
cloudflared tunnel route dns lg-karute karu7t3e.etzhayyim.com
# ingress configured in ~/.cloudflared/lg-karute-config.yaml:
#   - hostname: karu7t3e.etzhayyim.com
#     service: http://lg-karute.mitama-udf.svc.cluster.local:8080
cloudflared tunnel run lg-karute

# Update the DID Worker
cd 50-infra/karute-did-web
wrangler secret put XRPC_KARUTE_UPSTREAM   # value: https://karu7t3e.etzhayyim.com
wrangler deploy
```

## Logs

```bash
kubectl -n mitama-udf logs -f deploy/lg-karute -c server
kubectl -n mitama-udf logs -f deploy/lg-karute -c checkpointer
```

## Rollback

```bash
kubectl -n mitama-udf rollout undo deploy/lg-karute
```
