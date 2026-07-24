---
id: etzhayyim-sdk-checkpointer-readme
title: etzhayyim-sdk-checkpointer — TS sidecar container for MstCheckpointSaver
status: active
doc_type: how-to
topic: etzhayyim-sdk-checkpointer-sidecar
authoritative: true
last_verified: 2026-05-18
related:
  - ../../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md
  - ../../orgs/etzhayyim/com-etzhayyim-sdk/
  - ../../40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/checkpointer/
  - ../k8s/lg-uhl-right-neural/
---

# etzhayyim-sdk-checkpointer

Container image that runs the `@etzhayyim/sdk` checkpointer sidecar
(`etzhayyim-checkpointer`). Stage 2 of the pipeline declared in
**ADR-2605171800**: receive msgpack-framed checkpoint ops from a Python
LangGraph saver, project to atproto MST, return the root CID, then
enqueue async IPFS pin (Stage 3) and Base L2 anchor (Stage 4).

## Why a separate image

Per ADR-2605172100 the only seam allowed to import MST / IPFS / viem
clients is `@etzhayyim/sdk` (TS). Bundling it into every langserver
image would either:

1. Force every langserver to ship Node + the SDK runtime (bloats every
   Python/Rust/etc. image), or
2. Force every langserver to talk to a centralised checkpointer service
   (couples the substrate hot path to a network round-trip).

The K8s sidecar pattern — same Pod, shared emptyDir socket, separate
container — preserves substrate locality (sub-millisecond IPC) and
language isolation.

## Build

```bash
# From the repo root.
docker build -f 50-infra/etzhayyim-sdk-checkpointer/Dockerfile \
  -t ghcr.io/etzhayyim/etzhayyim-sdk-checkpointer:$(git rev-parse --short HEAD) \
  .
```

## Run (local TCP, for the integration test rig)

```bash
docker run --rm -it \
  -e ETZ_CHECKPOINTER_SOCKET=tcp://0.0.0.0:9100 \
  -e ETZ_CHECKPOINTER_ALLOWED_DIDS=did:web:uhl-right-neural.etzhayyim.com \
  -e ETZ_CHECKPOINTER_STATE_DIR=/tmp/etz-state \
  -p 9100:9100 \
  ghcr.io/etzhayyim/etzhayyim-sdk-checkpointer:dev
```

## Run (K8s sidecar, the standard topology)

See `50-infra/k8s/lg-uhl-right-neural/deployment.yaml`. The relevant
pieces:

- Shared `emptyDir` mounted at `/run/etzhayyim/` in both the langserver
  and sidecar containers — that's where the Unix socket lives.
- Shared `emptyDir` at `/var/etzhayyim/checkpointer-state` for the
  sidecar's persistent index / CAR staging.
- Both containers run as uid 65532 (matches the langserver Dockerfile's
  `USER` directive) so the socket is mutually rw without permission
  acrobatics.

## Environment contract

| Variable | Default | Required | Purpose |
|---|---|---|---|
| `ETZ_CHECKPOINTER_SOCKET` | `/run/etzhayyim/checkpointer.sock` | no | Unix path or `tcp://host:port` for the IPC server |
| `ETZ_CHECKPOINTER_STATE_DIR` | `<cwd>/state` | no | Local persistence for the saver index + staged CARs |
| `ETZ_CHECKPOINTER_ALLOWED_DIDS` | — | **yes** | Comma-separated DID allowlist. Requests with a non-listed `cell_did` are rejected. |
| `ETZ_IPFS_API_URL` | unset | no | When set, Stage 3 IPFS pinning is enabled |
| `ETZ_ANCHOR_CHAIN_ID` | unset | no | When set, Stage 4 Base L2 anchor batching is enabled |

## Security notes

- The `node_modules` install runs `--ignore-scripts` to block postinstall
  scripts from arbitrary npm packages. Our prod deps don't need them.
- No `.npmrc` is copied into the image. The local SDK dir contains an
  `.npmrc` with a GitHub PAT (untracked); `.dockerignore` excludes it.
- tini handles SIGTERM → `sidecar.stop()` so anchor batches in-flight
  get a chance to flush.

## Versioning

The sidecar wire protocol version is exposed as
`PROTOCOL_VERSION` in `@etzhayyim/sdk/checkpointer.d.ts`. The Python
saver pins the same constant (`MST_CHECKPOINT_PROTOCOL_VERSION`). Any
breaking change to envelope schema must bump both, in lockstep.
