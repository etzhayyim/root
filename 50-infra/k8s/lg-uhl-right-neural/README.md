---
id: lg-uhl-right-neural-readme
title: lg-uhl-right-neural — LangServer pod for uhl-right-neural Pregel
status: active
doc_type: how-to
topic: uhl-right-neural-langserver
authoritative: true
last_verified: 2026-05-18
related:
  - ../../../90-docs/adr/2605181000-uhl-right-neural-project.md
  - ../../../90-docs/adr/2605180900-unispsc-isic-langserver-actor-lexicon-xrpc-mcp.md
---

# lg-uhl-right-neural

LangServer pod serving the `uhl_right_neural` 16-vertex Pregel
(`kotodama.projects.uhl_right_neural.pregel:app`) over the standard
LangGraph CLI HTTP runtime.

Authoritative per **ADR-2605181000** (project charter) and follows the
four-call-surface pattern in **ADR-2605180900**.

## Files

| File | Role |
|---|---|
| `langgraph.json` | LangGraph CLI config — registers `uhl_pregel` graph |
| `Dockerfile` | Image build (Python 3.11-slim + langgraph-cli + kotodama) |
| `deployment.yaml` | k8s ServiceAccount + Deployment + Service (2-container pod: server + checkpointer sidecar) |

The Deployment is a **2-container pod** per ADR-2605171800: the
Python `server` container runs the LangGraph CLI; the TS
`checkpointer` sidecar runs `@etzhayyim/sdk/dist/checkpointer-bin.js`
on a shared `emptyDir`. The `MstCheckpointSaver` inside the Pregel
talks to the sidecar over `/run/etzhayyim/checkpointer.sock`. See
`50-infra/etzhayyim-sdk-checkpointer/` for the sidecar image.

## Build

```bash
# Repo root as build context (Dockerfile copies 40-engine/kotoba/crates/kotoba-kotodama/py).
docker build \
  -f 50-infra/k8s/lg-uhl-right-neural/Dockerfile \
  -t ghcr.io/etzhayyim/lg-uhl-right-neural:$(git rev-parse --short HEAD) \
  .

# Tag and push
docker push ghcr.io/etzhayyim/lg-uhl-right-neural:$(git rev-parse --short HEAD)
```

## Deploy

```bash
# Initial apply
kubectl apply -f 50-infra/k8s/lg-uhl-right-neural/deployment.yaml

# Pin a specific image after each build (or use the rollout pattern from
# 50-infra/k8s/lg-isin/README.md):
kubectl -n mitama-udf set image deployment/lg-uhl-right-neural \
  server=ghcr.io/etzhayyim/lg-uhl-right-neural:<commit-sha>
```

## Test (in-cluster)

```bash
# Port-forward
kubectl -n mitama-udf port-forward svc/lg-uhl-right-neural 8080:8080 &

# Health
curl -fsS http://localhost:8080/ok

# Invoke the uhl_pregel graph end-to-end (nerve aplasia branch)
curl -X POST http://localhost:8080/threads/runs \
  -H 'Content-Type: application/json' \
  -d '{
    "assistant_id": "uhl_pregel",
    "input": {
      "phenotype_input": {
        "patient_ref": "test-hash-abc12345",
        "side": "right",
        "age_years": 3.0,
        "onset": "congenital",
        "progressive": false,
        "locale_country": "JP"
      },
      "substrate_evidence": {"cn_fiber_count": 0}
    }
  }'
```

The response should include `substrate_decision.substrate_class = "nerve_aplasia"`
and `institution_match` containing ABI-capable institutions with
`requires_human_review: true`.

## Notes

- **No DATABASE_URL** — institution registry is in-package YAML (loaded via
  `importlib.resources`). P0 MVP is fully stateless.
- **No LLM key** — V12 plasticity / V13 outcome / V14 trial-design are stubs
  in P0. When P1 implements V13 (PyMC) and V14 (LLM-drafted protocol prose),
  add `ANTHROPIC_API_KEY` (or local model endpoint) to the deployment env.
- **Substrate pipeline status (ADR-2605171800)**:
  - **Stage 1 (saver)** — Python `MstCheckpointSaver` attaches via
    `MST_CHECKPOINT_SOCKET`. Live.
  - **Stage 2 (MST projection)** — TS sidecar in the same Pod. Live.
  - **Stage 2.5 (AEAD encryption, ADR-2605181100)** — per-cell symKey
    XChaCha20-Poly1305 sealing enabled via
    `ETZ_CHECKPOINTER_ENCRYPT_CELLS`. Every payload is ciphertext
    before it hits MST. Live.
  - **Stage 3 (IPFS pin)** — live. CAR files pinned to the fleet kubo
    at `simeonnomac-mini.local:5001` via `ETZ_IPFS_API_URL`. Pinned
    content is ciphertext only (Stage 2.5).
  - **Stage 4 (Base L2 anchor)** — implementation ready
    ([anchor-cron](../../anchor-cron/), local-anvil-validated), deploy
    pending. To go live: deploy `EtzhayyimAnchor.sol` to Base sepolia,
    fill `deps.toml [platform.l2.anchor_contract].address_testnet`,
    `kubectl apply -f 50-infra/anchor-cron/k8s/cronjob.yaml`, then
    uncomment `ETZ_ANCHOR_CHAIN_ID=84532` on this sidecar.
- **Sidecar state durability**: `/var/etzhayyim/checkpointer-state` is
  bound to the `lg-uhl-right-neural-checkpointer-state` PVC
  (ReadWriteOnce, 8Gi). The per-cell symmetric keys live here
  (`keys/<encodeURIComponent(cell_did)>.key`); losing them = losing
  the ability to decrypt every prior ciphertext pinned to IPFS.
  Set the underlying StorageClass to `Retain` reclaim policy in the
  cluster so a `kubectl delete deployment` cannot cascade into a key
  wipe. The PVC carries
  `etzhayyim.com/key-loss-is-irreversible: "true"` as a marker for
  operators + GitOps tooling.
- **Resource requests** are conservative (server: 100m CPU / 256Mi,
  sidecar: 50m CPU / 128Mi). Increase `limits.memory` when V09
  reprogramming / V13 PyMC models load larger parameter sets.
