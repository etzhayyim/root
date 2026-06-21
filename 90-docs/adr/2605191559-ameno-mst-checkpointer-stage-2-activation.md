---
id: 2605191559-ameno-mst-checkpointer-stage-2-activation
title: Ameno → MstCheckpointSaver Stage 2 activation (substrate persistence)
status: proposed
doc_type: adr
topic: ameno-substrate-persistence
authoritative: true
last_verified: 2026-05-19
depends_on:
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - 2605191257-ameno-daemon-path-b-kotodama-python
  - 2605191346-etzhayyim-vultr-free-murakumo-control-plane
related:
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605172000-etzhayyim-kotoba-substrate
---

# ADR 2605191559: Ameno → MstCheckpointSaver Stage 2 activation

## Context

Previous PRs(ADR-2605191257 + 2605191346)set up the lg-ameno K8s pod
as a 2-container topology(server + checkpointer sidecar)but the
Python server was still using **FileCheckpointer**(local JSON
snapshot on the PVC). The sidecar was running but unused.

Stage 1 = sidecar present, IPC socket + PVC mounted.
**Stage 2 = Python actually dials the socket and routes every
LangGraph checkpoint op through it.** That's this ADR.

`kotodama.checkpointer.MstCheckpointSaver` already exists(used by
`kotodama.projects.uhl_right_neural`、ADR-2605181000)so this is
**zero new substrate code** — just teaching `projects.ameno.pregel`
the same auto-attach trick.

## Decision

**`projects.ameno.pregel` adopts the `lg-uhl-right-neural` auto-attach
pattern.**

```python
def _maybe_mst_checkpointer() -> BaseCheckpointSaver | None:
    socket_path = os.environ.get("MST_CHECKPOINT_SOCKET")
    if not socket_path:
        return None
    cell_did = os.environ.get(
        "MST_CHECKPOINT_CELL_DID", "did:web:ameno.etzhayyim.com"
    )
    from kotodama.checkpointer import MstCheckpointSaver
    return MstCheckpointSaver(cell_did=cell_did, socket_path=socket_path)


app = build_graph(_maybe_mst_checkpointer())  # falls back to no-saver
```

`server.py` chooses the persistence layer at boot:

| env condition | checkpointer | CHECKPOINTER_KIND |
|---|---|---|
| `MST_CHECKPOINT_SOCKET` set | `MstCheckpointSaver` → sidecar → MST + IPFS + L2 anchor | `"mst"` |
| `MST_CHECKPOINT_SOCKET` unset | `FileCheckpointer(AMENO_HOME/checkpointer.json)` | `"file"` |

`/workerInfo` reports the active mode as `checkpointer: mst | file`.

### `lg-ameno` deployment env

`50-infra/k8s/lg-ameno/deployment.yaml` now sets:

```yaml
- name: MST_CHECKPOINT_SOCKET
  value: "/run/etzhayyim/checkpointer.sock"
- name: MST_CHECKPOINT_CELL_DID
  value: "did:web:ameno.etzhayyim.com"
```

The sidecar already runs with:

```yaml
- ETZ_CHECKPOINTER_ALLOWED_DIDS=did:web:ameno.etzhayyim.com
- ETZ_CHECKPOINTER_ENCRYPT_CELLS=did:web:ameno.etzhayyim.com
```

So every payload passing through the socket is AEAD-sealed with a
per-cell XChaCha20-Poly1305 key before MST projection
(ADR-2605181100).

### Effect by mode

| mode | server pod env | active persistence |
|---|---|---|
| **K8s `lg-ameno`** | both vars set | **MstCheckpointSaver → sidecar → MST/IPFS/L2** |
| **Path B native daemon** (laptop `python -m kotodama.projects.ameno`) | vars unset | FileCheckpointer (local JSON) |
| **Path A TS daemon** | n/a (TS doesn't reuse this) | TS FileCheckpointer (unchanged) |
| **Browser appview** | n/a | LocalCheckpointer (localStorage, unchanged) |

A single user with the K8s deploy gets substrate state; a single user
on laptop dev keeps local state. The browser appview's
`computeMode="daemon-b"` viewer connects to whichever daemon the URL
points to and inherits its persistence layer transparently.

### IPFS / L2 stages

`ETZ_IPFS_API_URL` and `ETZ_ANCHOR_CHAIN_ID` remain commented in the
sidecar env block — Stages 3-4 are the next gates:

- **Stage 3 (IPFS pin)**: flip when `simeonnomac-mini.local:5001` kubo
  is verified live from the etzhayyim-langserver namespace.
- **Stage 4 (L2 anchor)**: flip when `EtzhayyimAnchor` is deployed on
  Base sepolia and the `anchor-cron` CronJob is in place.

Both are infrastructure-side changes; no further kotodama edits
required.

## Consequences

- ameno joins the artificial-organism substrate persistence on equal
  footing with `uhl-right-neural`. Same MST projection, same encryption
  envelope, same future anchor pipeline.
- **The Path A / Path B split is no longer pure-local-only**: deployed
  in K8s, Path B becomes a substrate-anchored worker. Local dev (no
  K8s) still works unchanged.
- ADR-2605172000 (kotoba) is upheld: this Python module imports zero
  MST / IPFS / viem code; the sidecar is the only seam, per
  ADR-2605172100.
- ADR-2605181100 (encrypted records) is upheld: PII in graph state
  (chat history, tool results, predictions) is AEAD-sealed before
  reaching MST.
- The browser viewer (ADR-2605191407) and the swarm
  (ADR-2605191524) **stay browser-side** — substrate sync between
  browser LocalCheckpointer and daemon MstCheckpointSaver is a
  separate follow-up (likely a new "memory-vault MST projector" ADR).

## Alternatives Considered

1. **Continue using FileCheckpointer in the pod** — sidecar would be
   dead weight. Already paying for the container, may as well wire it.
2. **Skip env auto-attach, force MstCheckpointSaver always** — breaks
   the laptop dev path (`python -m kotodama.projects.ameno`
   immediately fails to dial a socket that isn't there).
3. **Re-implement MstCheckpointSaver inside `projects.ameno`** —
   `kotodama.checkpointer` already does this; duplicating costs
   maintenance.

## References

- ADR-2605171800 (LangGraph → MstCheckpointSaver → MST → IPFS → L2)
- ADR-2605181000 (uhl-right-neural, the auto-attach pattern source)
- ADR-2605181100 (MST encrypted records)
- ADR-2605191257 (Path B Python port, Stage 1 sidecar)
- ADR-2605191346 (etzhayyim Vultr-free)
- `kotodama.checkpointer.MstCheckpointSaver`(既存実装)
- `@etzhayyim/sdk` checkpointer entrypoint(既存実装)
