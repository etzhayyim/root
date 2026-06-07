---
id: adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
title: "ADR-2605171800: Artificial Organism Ecosystem — LangGraph Pregel → MstCheckpointSaver → atproto MST → IPFS → Base L2 anchor pipeline"
status: proposed
doc_type: adr
topic: langgraph-mst-ipfs-l2-anchor-pipeline
authoritative: true
last_verified: 2026-05-17
priority: 7.0
axis: architecture
weight: 0.70
priority_note: "Defines the durable-state and verifiability spine for the artificial organism ecosystem (magatama actors). Touches every cell-class actor in 20-actors/magatama. Active once first reference impl lands; this ADR is the contract."
authoritative_for:
  - artificial organism checkpoint pipeline (Pregel → MstCheckpointSaver → MST → IPFS → L2)
  - LangGraph MstCheckpointSaver usage convention for organism cells (Python thin shim + TS sidecar via @etzhayyim/sdk)
  - MST projection schema (atproto-compatible, standalone — no PDS coupling)
  - L2 anchor target (Base) and batching semantics
  - IPFS pinning responsibility split
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
related:
supersedes: []
superseded_by: []
---

# ADR-2605171800: Artificial Organism Ecosystem — LangGraph Pregel → MstCheckpointSaver → atproto MST → IPFS → Base L2 anchor pipeline

**Status**: proposed
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

# Context

`20-actors/magatama` hosts the Pregel framework that runs **artificial organism cells**: LangGraph-driven actor processes whose state evolves over BSP super-steps. The Bonsai Cultivar series (ADR-2605091300, ADR-2605092000, ADR-2605092100, ADR-2605092200) frames these cells as a living ecosystem — each cell has metabolism, lineage, fission, and a measurable phenotype.

For that metaphor to hold up in production, every cell's state must be:

1. **Durable** — survives crashes / migrations / scale-down. LangGraph normally solves this with `PostgresSaver` (the canonical checkpoint saver from `langgraph-checkpoint-postgres`), but ADR-2605172000 (RW-free substrate) prohibits centralized off-chain DBs in this monorepo. This ADR provides a substrate-compliant equivalent.
2. **Replayable** — any past super-step can be reconstructed deterministically.
3. **Verifiable** — a third party (auditor, peer cell, off-chain observer) can confirm a given state existed at a given step without trusting our infrastructure.
4. **Content-addressed** — large blobs (LoRA weights, embedding tensors, observation buffers, tool outputs) live by hash, not by mutable pointer.
5. **Finalizable** — at coarse intervals, a checkpoint root is anchored on-chain so the chain of state has a public, immutable history.

A plain LangGraph checkpoint saver (memory or Postgres) only satisfies (1)–(2), and Postgres specifically is disallowed here per ADR-2605172000. The remaining three properties — plus substrate compliance — are what this ADR delivers via `MstCheckpointSaver`.

## Why MST, IPFS, and an L2 — directly as the LangGraph saver, not as projection from Postgres?

| Property | `MemorySaver` (LG default) | `PostgresSaver` (prohibited here per ADR-2605172000) | **`MstCheckpointSaver`** (this ADR) |
|---|---|---|---|
| Durable across restart | ❌ | ✅ | ✅ (IPFS + L2 anchor) |
| Replayable | ⚠️ (in-process only) | ✅ | ✅ |
| Verifiable by third party | ❌ | ❌ (trust DB owner) | ✅ (Merkle proof against on-chain root) |
| Content-addressed | ❌ | ❌ | ✅ |
| Public, immutable history | ❌ | ❌ | ✅ |
| Federable with atproto ecosystem | ❌ | ❌ | ✅ (atproto-shaped MST + CAR) |
| Cell can migrate between hosts without coordination | ❌ | ⚠️ | ✅ (IPFS-addressed state, anchor as ground truth) |
| Compliant with ADR-2605172000 substrate boundary | ✅ (no state) | ❌ | ✅ |

The MST + IPFS + L2 trio is also exactly the shape atproto uses for its repo (MST → CAR → optional anchor). Adopting an **atproto-compatible MST projection** means each organism cell is automatically compatible with atproto tooling (`@atproto/repo`, CAR readers, MST verifiers, ipld libraries), which the religious-corp open ecosystem already uses (`10-protocol/at-client`, `50-infra/k8s/atproto-pds`, `60-apps/etzhayyim-project-atproto`).

An earlier draft of this ADR routed all checkpoints through `PostgresSaver` first and projected to MST asynchronously. That draft was superseded by the present design before any reference impl landed, because ADR-2605172000 prohibits Postgres in this monorepo. The new design folds projection *into* the saver itself: `MstCheckpointSaver.put()` writes directly to the MST/IPFS layer via a TS sidecar (`@etzhayyim/sdk`) over a local Unix socket. The LangGraph hot path now has exactly one substrate hop instead of two.

## Why standalone MST, not the PDS?

`50-infra/k8s/atproto-pds` exists and could be the canonical store for organism state. We chose **standalone, atproto-compatible MST** instead:

- **Decoupling**: a PDS is opinionated about authentication, rate limits, repo structure, federation semantics. Organism cells run as Pregel super-steps at >>1 Hz; force-fitting that into PDS commit cadence couples cell metabolism to PDS internals.
- **No federation gate**: standalone MST lets us publish organism state at whatever cadence and granularity suits the cell. The PDS path can be added later as a publishing surface (e.g., the cell exports a curated subset of its state as PDS records).
- **Same on-disk shape**: by using `@atproto/repo`'s MST library directly (not its PDS server), we get atproto-compatibility for free without coupling to PDS lifecycle.
- **Public/private split**: religious-corp activity has both. Standalone MST per cell lets us decide publication policy per cell, not per PDS instance.

## Why Base L2?

- **EVM-equivalent** — standard Solidity tooling, viem/ethers/foundry, no learning cost.
- **Optimistic rollup on Ethereum** — security inherited from L1.
- **Cheap calldata** — anchor cost dominated by calldata (~32 bytes for a CID + a few words for metadata); Base calldata pricing keeps per-anchor cost in the cents range at typical organism cadence.
- **Production-stable** — public RPC, Etherscan-equivalent (Basescan), bridges, Coinbase custody for treasury.
- **No bridging required for write-only anchor** — we only need to publish a transaction; we don't need to pull tokens out.
- **Easy to swap** — the anchor contract is ~50 lines of Solidity; if we ever move to OP Mainnet, Optimism, Linea, or back to L1, only the deploy target changes.

`geth-private` is mentioned in `CLAUDE.md` but not yet scaffolded. Local geth is useful for unit tests and pre-deploy rehearsal, but production anchor goes to Base.

# Decision

Adopt the following four-stage pipeline for every magatama organism cell that needs verifiable durable state. The pipeline is **append-only**: each stage adds artifacts; nothing is overwritten. Stages 1–2 are synchronous (Pregel hot path); Stages 3–4 are async.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Stage 1 — LangGraph Pregel super-step                              │
│  (cell.invoke / cell.stream — BSP boundaries)                       │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ checkpoint(t)  [Python side]
┌─────────────────────────────────────────────────────────────────────┐
│  MstCheckpointSaver (Python, BaseCheckpointSaver subclass)          │
│  • serialises checkpoint → msgpack                                  │
│  • IPC over Unix socket → TS sidecar                                │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ socket /run/etzhayyim/checkpointer.sock
┌─────────────────────────────────────────────────────────────────────┐
│  Stage 2 — @etzhayyim/sdk checkpointer sidecar (TypeScript)         │
│  • @atproto/repo: build deterministic MST → CAR                     │
│  • emits mst_root_cid synchronously to caller (saver receipt)       │
│  • enqueues CAR for IPFS pin (Stage 3) and L2 anchor (Stage 4)      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ async pin
┌─────────────────────────────────────────────────────────────────────┐
│  Stage 3 — IPFS                                                     │
│  CAR pinned to local kubo + remote pinning service                  │
│  Large blobs (>blob_inline_threshold) deduplicated by CID           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ batched anchor (configurable cadence)
┌─────────────────────────────────────────────────────────────────────┐
│  Stage 4 — Base L2 — CheckpointAnchor.sol                           │
│  emit Anchored(did, mst_root_cid, checkpoint_id, ts)                │
│  anchor-cron records tx_hash, block, log_index in saver state       │
└─────────────────────────────────────────────────────────────────────┘
```

Each stage is independently replayable from the previous stage's artifacts. The chain of cryptographic links is:

```
state(t)  ─msgpack─▶  Python saver call
                              │
                              ▼ (IPC, in-host)
                     atproto MST root CID  ◀── CAR file (deterministic encode)
                              │
                              ▼
                     IPFS-pinned CAR (content-addressed; CID identity = MST root identity)
                              │
                              ▼
                     L2 tx calldata contains (did, mst_root_cid, checkpoint_id, ts)
                              │
                              ▼
                     Tx mined → block hash → L1 calldata batch → L1 finality
```

Postgres / Kotoba/Datomic / Kysely do not appear anywhere in this pipeline. Per ADR-2605172000, the substrate is exhausted by MST + IPFS + L2.

## Stage 1 — LangGraph Pregel runtime + Python saver shim (host: `20-actors/magatama`)

Each cell is a LangGraph graph constructed with the magatama host SDK. Super-step boundaries are defined by LangGraph's normal `interrupt_after` / `interrupt_before` semantics and by the cell's BSP scheduler.

**Convention**: every cell graph builds with `checkpointer=MstCheckpointSaver(socket_path=..., cell_did=...)`. The saver is a thin (~50 LOC) `langgraph.checkpoint.base.BaseCheckpointSaver` subclass living at:

```
20-actors/magatama/py/src/pymagatama/checkpointer/mst_saver.py
```

It implements `put` / `get_tuple` / `list` / `put_writes` by:

1. Serialising the checkpoint payload to **msgpack** (binary, deterministic).
2. Opening (or reusing) a connection to the Unix socket at `socket_path` (default: `/run/etzhayyim/checkpointer.sock`).
3. Sending a length-prefixed msgpack request `{op, cell_did, thread_id, checkpoint_ns, checkpoint_id, payload}` and awaiting the response.
4. Returning the LangGraph-expected tuple unchanged on the Python side. The saver holds **no MST / IPFS / viem logic** — all substrate code lives TS-side per ADR-2605172100 ("Substrate client imports | Only via `@etzhayyim/sdk`").

IPC schema (msgpack, request / response framed by 4-byte big-endian length prefix):

```
Request  := { v: 1, op: "put" | "get_tuple" | "list" | "put_writes",
              cell_did: str, thread_id: str, checkpoint_ns: str,
              checkpoint_id: str | null, payload: bytes, meta: {…} }
Response := { ok: bool, mst_root_cid: str | null,
              data: bytes | null, error: str | null }
```

Unix socket is preferred over TCP/HTTP for (a) zero-copy via SOCK_STREAM, (b) host-local-only by construction (filesystem permission as access control), (c) sub-millisecond round-trip vs ~1ms HTTP/1.1. For non-co-located deployment (test rigs running saver against a remote sidecar) the same wire format works over TCP; the saver accepts `socket_path=tcp://host:port`.

## Stage 2 — `@etzhayyim/sdk` checkpointer sidecar (TypeScript)

A long-lived Node.js process (one per magatama host) shipped as part of `20-actors/etzhayyim-sdk`. Source layout:

```
20-actors/etzhayyim-sdk/src/checkpointer.ts   — sidecar entrypoint + IPC server + MST commit
```

Responsibilities, on each `op="put"` request:

1. msgpack-decode the request body.
2. **Project** the checkpoint payload to an atproto MST. Projection rules (deterministic; same payload → same CID, bit-for-bit):
   - MST key namespace: `magatama.cell.{cell_did_suffix}/checkpoint/{checkpoint_id}`.
   - Each top-level LangGraph state key becomes a record under `magatama.cell.{…}/state/{key}`.
   - LangGraph channel writes (the per-step delta) go under `magatama.cell.{…}/channel/{step}/{channel}`.
   - Records >`blob_inline_threshold` bytes (default 16 KiB) become **separate blobs**, referenced by CID in the MST record. Below threshold, inlined as record content.
3. Build the MST with `@atproto/repo` and serialise to **CAR v1** with canonical block ordering.
4. Compute the MST **root CID** and return it synchronously to the Python saver in the response.
5. Enqueue the CAR for asynchronous IPFS pinning (Stage 3) and L2 anchor batching (Stage 4) in an on-disk durable queue (`~/.etzhayyim/checkpointer/queue/{cell_did}/{checkpoint_id}.car`).
6. Maintain a small **saver state index** (BoltDB / level / plain SQLite — implementation choice, not load-bearing) so `op="get_tuple"` and `op="list"` can be served without re-walking the queue. This is the **only** local persistence; it holds nothing that isn't also derivable from IPFS-pinned CARs.

Projection is **pure**. This is how third parties verify replay.

The sidecar is **not a database**. Its on-disk state is a write-ahead spool plus a derived index; both can be reconstructed at any time by walking the host's IPFS pins for the cell's DID. The substrate of record is still IPFS + Base L2.

Cell DID is provided by the saver on every call (`cell_did` field). The sidecar refuses requests for any DID it has not been provisioned to anchor for (see § "Cell DID provisioning").

## Stage 3 — IPFS pinning (`50-infra/ipfs-pinner`, or service of choice)

The sidecar drains its pin queue to:

1. **Local IPFS node** (Kubo or Helia, deployed in `50-infra/ipfs/` — currently absent; to be scaffolded in a follow-up).
2. **Remote pinning service** (configurable: web3.storage, Filebase, or Cloudflare R2 with IPFS gateway). At least one remote pin is required for durability.

On successful pin, the sidecar updates its saver-state index with `ipfs_pinned_at`, `ipfs_pin_service`, `ipfs_pin_id`.

Large blobs referenced from MST records are pinned **independently** by CID (deduplication: identical embeddings or LoRA weights pinned once across all cells).

## Stage 4 — Base L2 anchor (`50-infra/l2-anchor-contract` + `50-infra/anchor-cron`)

A simple Solidity contract on Base mainnet (chain id 8453):

```solidity
// 50-infra/l2-anchor-contract/src/CheckpointAnchor.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.24;

contract CheckpointAnchor {
    event Anchored(
        bytes32 indexed cell_did_hash,    // keccak256(cell_did) — index-friendly
        string  cell_did,                  // full DID string, in data (not indexed)
        bytes   mst_root_cid,              // multibase-encoded CID bytes (base32 CIDv1)
        string  checkpoint_id,             // LangGraph checkpoint_id (ULID/UUID)
        uint64  cell_timestamp_ms          // wall-clock time at checkpoint
    );

    /// @notice Anchor a single checkpoint root.
    /// @dev Anyone can call; the event is the only state. The contract is
    ///      intentionally permissionless and stateless — the chain itself is
    ///      the only state. Identity comes from the DID resolution, not the
    ///      contract.
    function anchor(
        string calldata cell_did,
        bytes  calldata mst_root_cid,
        string calldata checkpoint_id,
        uint64 cell_timestamp_ms
    ) external {
        emit Anchored(
            keccak256(bytes(cell_did)),
            cell_did,
            mst_root_cid,
            checkpoint_id,
            cell_timestamp_ms
        );
    }

    /// @notice Anchor multiple checkpoint roots in one tx (batched cadence).
    function anchorBatch(
        string[] calldata cell_dids,
        bytes[]  calldata mst_root_cids,
        string[] calldata checkpoint_ids,
        uint64[] calldata cell_timestamps_ms
    ) external {
        uint256 n = cell_dids.length;
        require(
            n == mst_root_cids.length &&
            n == checkpoint_ids.length &&
            n == cell_timestamps_ms.length,
            "len mismatch"
        );
        for (uint256 i = 0; i < n; i++) {
            emit Anchored(
                keccak256(bytes(cell_dids[i])),
                cell_dids[i],
                mst_root_cids[i],
                checkpoint_ids[i],
                cell_timestamps_ms[i]
            );
        }
    }
}
```

**Design properties**:

- **Stateless** — no storage writes; the chain log itself is the canonical record. Per-anchor gas is ~event-emit overhead only.
- **Permissionless** — anyone can call. Authority comes from the DID resolving to a key the caller controls; an unauthorized anchor for a DID-you-don't-control is a useless log entry (peers ignore it). This sidesteps having a privileged role to manage.
- **Batchable** — `anchorBatch` lets the anchor-cron submit N anchors in one tx (calldata-dominated cost, so batching is roughly linear in calldata not per-event).
- **No upgrade proxy** — if the schema changes, deploy v2 with a new address and migrate the cron. Anchors-as-events means there's no migration of contract state.

`50-infra/anchor-cron` runs every `anchor_period` (default 60s; configurable per cell-cohort):

1. Reads the checkpointer sidecar's saver-state index for entries with `ipfs_pinned_at IS NOT NULL AND anchor_tx_hash IS NULL`, grouped by cell DID, up to a batch cap (default 100 entries per tx). The index is queried over the same Unix socket via `op="anchor_pending"`.
2. Constructs `anchorBatch(...)` calldata.
3. Signs with the **organism anchor key** (separate from `did:web:etzhayyim.com` controller key; this is a hot key funded with Base ETH).
4. Submits to Base; waits for 1 confirmation; writes `anchor_tx_hash`, `anchor_block_number`, `anchor_log_index`, `anchored_at` back into the sidecar's index via `op="anchor_commit"`.
5. On revert / gas-price spike, backs off exponentially and retries.

Anchor cadence is tunable per cohort. Defaults:

| Cell cohort | Anchor cadence | Rationale |
|---|---|---|
| Public organism cells (open data, public governance) | every 60s | Public verifiability is the point |
| Private cells (internal-only) | every 300s | Lower public stake → batch more aggressively |
| Ephemeral test cells | never | Anchor opt-in via cohort config |

## Cell DID provisioning

Every anchorable cell needs a DID. Two tiers:

- **`did:web:etzhayyim.com`** — the operating-entity root DID (LIVE per ADR-2605152100 step 10). Cells operating *as* the religious corp use this DID directly.
- **Per-cell DIDs** — `did:plc:…` or `did:key:…` issued per cell, with the operating-entity DID as a controller in the DID document. Required for cells that need independent key custody (e.g., long-running personal-assistant cells).

DID issuance for per-cell DIDs is out of scope for this ADR; it gets its own follow-up. Until then, cells anchor under `did:web:etzhayyim.com` with a cohort discriminator in `cell_timestamp_ms` metadata.

## Verification semantics (third-party replay)

A third party with only `(did, anchor_tx_hash)` can:

1. Read the Base tx, decode the `Anchored` event → `(mst_root_cid, checkpoint_id, ts)`.
2. Fetch the CAR file from any IPFS gateway by `mst_root_cid`.
3. Parse the CAR using `@atproto/repo` or any standard ipld/dag-cbor tooling.
4. Walk the MST to reconstruct cell state at the checkpoint.
5. Verify CID match end-to-end: re-serialize the parsed MST → CID matches the on-chain anchor.

No trust in our Postgres, our IPFS pinner, or our daemons is required. Only Base finality + content-addressed IPFS + the public CID hash function are trusted.

## Failure modes and recovery

| Stage failure | Consequence | Recovery |
|---|---|---|
| Sidecar Unix socket unreachable (process dead) | Python saver `put()` raises; LangGraph treats checkpoint as not persisted; retries per LangGraph semantics. No cell state lost in-memory. | Restart sidecar (systemd / k8s liveness probe). Saver auto-reconnects on next call. |
| Sidecar CAR write to local disk fails | Saver returns error; LangGraph retry. | Investigate disk pressure; sidecar is bounded by `~/.etzhayyim/checkpointer/queue` size which an operator can monitor. |
| IPC schema mismatch (Python ↔ TS version skew) | `op` rejected with `error: "unknown op"`. | Pin both sides on the same `@etzhayyim/sdk` version; CI gate (future) verifies cross-language schema parity. |
| MST projection bug → wrong CID | Anchored CID points at corrupted CAR. | Anchors are append-only logs; we cannot un-anchor. Issue a `corrupted=true` follow-up anchor referencing the bad one + the corrected CID. Verifiers prefer latest non-corrupted anchor per (did, checkpoint_id). Golden-CAR tests in CI prevent the bug class. |
| IPFS pin fails | `ipfs_pinned_at` stays NULL in saver-state index; anchor blocked for this entry. | Sidecar retries with exponential backoff; pin to alternate service if primary down. |
| Anchor tx reverts / underprices | `anchor_tx_hash` stays NULL; entry eligible for next batch. | Anchor-cron retries with re-priced gas; circuit breaker if RPC unreachable. |
| Base RPC down | Anchor-cron pauses; sidecar pin-queue grows on disk. | Self-heals when RPC recovers; backlog auto-drains. |
| Anchor key compromised | Attacker can post arbitrary `Anchored` events under our DID. | Rotate the key in the DID document; peers/verifiers reject anchors with old key. The actual cell state in IPFS is unaffected — only the *public claim* layer is impacted. |
| Sidecar saver-state index lost (disk corruption) | `op="get_tuple"` / `op="list"` return empty until rebuild. | Walk the host's IPFS pins for this cell's DID and rebuild the index. The index is derived, not authoritative. |

## Repository layout (target — scaffolded alongside this ADR's revise)

```
20-actors/magatama/py/src/pymagatama/
  checkpointer/             # NEW — Python BaseCheckpointSaver shim
    __init__.py
    mst_saver.py            # MstCheckpointSaver (~50 LOC, IPC over Unix socket)

20-actors/etzhayyim-sdk/
  src/
    checkpointer.ts         # NEW — TypeScript sidecar (IPC server + MST + queue)
  bin/
    etzhayyim-checkpointer  # NEW — sidecar launcher (node-based)

50-infra/
  ipfs-pinner/              # existing scaffold (Stage 3); consumed by sidecar
  l2-anchor-contract/       # existing scaffold (Stage 4); Foundry project
  anchor-cron/              # existing scaffold (Stage 4); reads via op="anchor_pending"
  ipfs/                     # MISSING from CLAUDE.md — to be scaffolded (Kubo manifests)

60-apps/
  organism-demo/            # NEW — single-cell PoC consuming the pipeline
```

Note the absence of `50-infra/mst-projector/` — the projector daemon from the original draft is gone. Its role is folded into the `@etzhayyim/sdk` checkpointer sidecar, which is the only IPC peer Python ever talks to for checkpoint state.

# Consequences

## 正の効果

- **Third-party verifiable organism state.** Auditors, peer cells, external researchers can confirm "cell X had state Y at checkpoint Z" with only public artifacts. This is the foundation for the religious-corp public-interest claim that "open" means open-in-the-strong-sense.
- **Cell migration is cheap.** Move a cell between hosts → ship its DID + IPFS pins; new host re-binds to its Postgres or rebuilds Postgres state from the CAR. No coordination with central authority.
- **atproto ecosystem compatibility.** Standard tooling (`@atproto/repo`, CAR readers, IPLD libs) reads organism state. Bridge to PDS publication is a future ADR away.
- **Composable with Bonsai Cultivar metaphor** (ADR-2605091300). Cells have lineage (anchor chain), metabolism (rate of MST growth), and reproduction (fission = copy CAR + fork DID). All measurable from public artifacts.
- **No supplier lock-in.** IPFS, Base, and atproto MST are all open standards / open-source. Anchor contract is 50 lines of permissive-license Solidity.
- **Substrate compliance for free.** The saver is the only piece of LangGraph integration; once it's in place, every cell on every magatama host is automatically ADR-2605172000 / 2605172100 compliant. No leakage of `@atproto/api` or `viem` imports into Python or app code.
- **Failure isolation.** The Python saver's only synchronous dependency is the TS sidecar over Unix socket. MST/IPFS/L2 latencies are absorbed by the sidecar's queue; a slow IPFS pin or a stalled Base RPC does not slow the Pregel super-step beyond the local MST commit.
- **Single-language substrate.** All MST + IPFS + viem code lives in TypeScript via `@etzhayyim/sdk`. Tests, type-checks, and security review concentrate in one place rather than being duplicated across Python and TS.

## 負の効果 / コスト

- **Operational surface area: 1 new sidecar + 3 existing services**: `@etzhayyim/sdk` checkpointer sidecar (new), IPFS pinner (+ IPFS node), anchor cron, and the deployed Base contract. The sidecar is a long-lived Node.js process per magatama host — needs a systemd unit / k8s sidecar container, a healthcheck, and a restart policy. The previous draft's separate MST projector daemon is gone, so net process count is the same as the draft (4 → 4) but with one fewer IPC peer.
- **L2 anchor cost.** At 60s cadence per cell with batching, rough order-of-magnitude is $0.01–$0.10 per cell per day on Base (calldata-dominated). Cheap individually, but linear in cell count. For 10⁴ cells: ~$100–$1000/day. Mitigation: longer batch periods, IPFS-as-default + opt-in anchor per cohort, future move to a data-availability layer if scale demands it.
- **Hot anchor key custody.** A wallet funded with Base ETH that signs anchor txs must be protected. Mitigation: HSM or threshold signature; rotation procedure in the DID document.
- **Standalone MST cannot federate via PDS-relay.** Cells are not visible in atproto firehoses unless we add a publishing surface. Acceptable for v1 (verifiability ≠ federation); future ADR can add a PDS export.
- **MST projection determinism is load-bearing.** A bug that changes block ordering or encoding silently breaks reproducibility. Mitigation: golden-CAR tests in CI, snapshot tests across `@atproto/repo` upgrades. With projection happening in one place (the TS sidecar), there's exactly one codepath to gate.
- **Python ↔ TS IPC schema drift risk.** If `@etzhayyim/sdk` and `pymagatama.checkpointer` versions skew on the wire, the saver fails closed (`error: "unknown op"`). Mitigation: pin compatible versions in `deps.toml`; future CI gate runs both sides against a shared msgpack schema fixture.
- **IPC adds ~hundreds of µs per super-step.** Unix socket round-trip + msgpack encode/decode. Negligible at expected cell rates (<10 Hz/cell) but measurable; budget appropriately for high-cadence cohorts.
- **IPFS unpinning risk.** If both local and remote pin lapse, the CAR is unreachable, but the anchor on Base still claims its CID. Mitigation: pinning service redundancy + monitoring + Filecoin deal as cold tier (future).

## Out of scope for this ADR

- DID issuance protocol for per-cell DIDs (separate follow-up ADR).
- Cross-cell synchronization / consensus (per-cell anchors are independent).
- LangGraph state schema (per-cell; each cell graph defines its own state).
- LoRA / FP8 vector substrate (ADR-2605092000 — referenced for context only).
- PDS-publication of organism state (future ADR; the standalone MST can be republished into the PDS as records).
- Filecoin / Arweave cold tier for IPFS blobs.
- Anchor contract upgrades / governance (current contract is permissionless and replaceable by deploying v2 at a new address).

## Migration / rollout plan

This ADR is the **contract**, accompanied by Phase-1 scaffolds. Rollout is staged:

- [x] **Phase 0 — this ADR (revise).** Contract published with PostgresSaver dropped in favour of `MstCheckpointSaver`.
- [ ] **Phase 1 — reference impl scaffolds (this revise).** Python `MstCheckpointSaver` shim in `20-actors/magatama/py/src/pymagatama/checkpointer/`, TS sidecar in `20-actors/etzhayyim-sdk/src/checkpointer.ts`. Both compile / lint clean; no end-to-end test yet.
- [ ] **Phase 2 — wire end-to-end on Base sepolia.** Local kubo + sepolia anchor-cron + a single cell from `60-apps/organism-demo/`.
- [ ] **Phase 3 — magatama host integration.** Host SDK passes `cell_did` into the saver constructor on every cell session start.
- [ ] **Phase 4 — Base mainnet deploy.** Deploy `CheckpointAnchor.sol` on Base mainnet. Address recorded in `deps.toml` under `[platform.l2_anchor]`. Wallet funded.
- [ ] **Phase 5 — first production cell.** A real cell from an `60-apps/etzhayyim-project-open-*` project opts into the pipeline. Monitor cost + latency for one week.
- [ ] **Phase 6 — IPFS infra scaffolded.** `50-infra/ipfs/` Kubo deployment (currently missing from layout in `CLAUDE.md`).
- [ ] **Phase 7 — `lefthook.yml` `adr-validate` hook** ensures any ADR claiming `authoritative_for` overlapping this one is properly chained via `supersedes`, plus IPC schema parity check (Python msgpack codec ↔ TS msgpack codec).

# Alternatives Considered

## A. Postgres-only (no MST, no IPFS, no anchor)

LangGraph + PostgresSaver, done. Cells are durable and replayable.

却下理由: directly prohibited by ADR-2605172000 (RW-free substrate) in this monorepo. Even ignoring the substrate rule, this approach fails third-party verifiability, content-addressability, and public history. The organism metaphor's "open" property collapses to "trust the operator." This is the same failure mode that motivates ADR-2605152100's source-control boundary — we want the open ecosystem to be *demonstrably* open, not just nominally so. If a future use case needs Postgres-grade query performance (e.g., HITL workflows requiring rich filtering), the route is XRPC consent-capability into an upstream backend, not a Postgres on the open side.

## B. Atproto PDS as canonical store

`50-infra/k8s/atproto-pds` is already deployed (per CLAUDE.md). Use it as the canonical store; each cell is an atproto repo; checkpoints are repo commits.

却下理由: couples cell cadence to PDS commit rate, forces every cell to look like an atproto identity (heavyweight for short-lived cells), and bakes federation policy into the data layer. The MST is the useful primitive, not the PDS; we adopt the primitive without the package. PDS publication can be added later as a publishing surface (Phase 6+).

## C. PostgresSaver + async MST projector daemon (original draft of this ADR)

The earlier draft of this ADR kept upstream `PostgresSaver` on the hot path and projected to MST asynchronously via a `pg_notify`-driven Node daemon, with a Postgres sidecar table tracking projection / pin / anchor state per checkpoint.

却下理由: ADR-2605172000 prohibits Postgres in this monorepo, so the entire upper half of that pipeline is non-starter. Beyond the substrate rule, the original draft had two practical drawbacks the new design fixes:
- Two substrate hops per super-step (Postgres write, then projection daemon read) instead of one.
- A separate daemon (`50-infra/mst-projector`) duplicating concerns that already live in `@etzhayyim/sdk`.

The chosen design (`MstCheckpointSaver` thin shim + TS sidecar via Unix socket) preserves the *spirit* of the original — keep the hot path simple, do projection close to the saver — while complying with the substrate boundary and removing a process.

## D. L1 Ethereum anchor (not L2)

Anchor directly on Ethereum mainnet for strongest finality.

却下理由: cost. At ~$1–$10 per anchor on L1, the calculus breaks at any nontrivial cell count. Base inherits L1 finality with one extra week of fraud-proof window — acceptable for organism state where finality-with-latency is the norm anyway.

## E. zkEVM L2 (Polygon zkEVM, Linea, zkSync Era)

zk rollups give validity (not fraud) proofs, which is stronger than optimistic rollups.

却下理由: higher cost per byte, less mature tooling at the time of writing, and the validity guarantee is overkill for an append-only event log. Optimistic-rollup security is more than sufficient for "did this CID exist at this time." Reconsider if anchor verification has strict latency requirements (which it doesn't for organism state).

## F. Local geth-private only (no public L2)

CLAUDE.md mentions `geth-private` (not yet scaffolded). Run a private chain; anchor locally.

却下理由: defeats the verifiability property. A private chain is just another database we operate. Useful as a *test* target during development; not as the production target.

## G. Sign checkpoints with the DID key, skip the chain entirely

DID-signed checkpoint receipts, no anchor.

却下理由: signatures alone don't give immutable public history (we could re-sign different state with the same key and timestamp), and there's no fork-detection. The anchor is precisely what provides cross-time consistency. Signatures+anchor would be stronger, but the anchor alone is sufficient because the CID *is* the commitment.

## H. Use IPLD without atproto MST shape

Project to plain IPLD DAGs (e.g., dag-cbor) without committing to atproto's MST structure.

却下理由: atproto-shape MST gets us free ecosystem compatibility (PDS bridge, CAR tooling, future federation). The cost is following atproto's MST encoding conventions, which is a small surface area. Net positive.

## I. Filecoin / Arweave instead of IPFS pinning

Permanent storage instead of pinning.

却下理由: paid-up-front cost model is poorly matched to the high-churn early phase. Pinning + future Filecoin cold tier is the cheaper path. Revisit when access patterns are understood.

## J. Python-native MST + IPFS + viem port (no TS sidecar)

Reimplement `@atproto/repo`'s MST, kubo client, and viem-equivalent L2 calldata builder in pure Python. `MstCheckpointSaver` becomes a one-process saver with no IPC.

却下理由: violates ADR-2605172100 ("Substrate client imports | Only via `@etzhayyim/sdk`"), which exists precisely to avoid two parallel substrate stacks. The MST encoding is determinism-sensitive — divergence between Python and TS at the bit level silently breaks third-party verification. The TS ecosystem also has `@atproto/repo`, `viem`, and `kubo-rpc-client` as battle-tested upstream; Python equivalents either don't exist or are immature. The IPC hop is sub-millisecond on Unix socket — cheap compared to the IPFS pin and L2 anchor latencies that dominate the pipeline. Revisit only if (a) `@etzhayyim/sdk` itself migrates to a non-TS host language, or (b) magatama moves to a runtime where IPC has macro-cost (unlikely on Linux hosts).

## K. Kotoba/Datomic as the saver

Use `langgraph-checkpoint-postgres` against a Kotoba/Datomic Postgres-compatible endpoint, leveraging its streaming materialised views for downstream projection.

却下理由: identical to (A) under ADR-2605172000; Kotoba/Datomic is the specific exemplar of the prohibited category. If RW-grade streaming is needed for an upstream workflow, run RW upstream and call it via XRPC consent-capability; do not embed it on the open side.

# References

- LangGraph PostgresSaver — https://langchain-ai.github.io/langgraph/concepts/persistence/#postgres
- `langgraph-checkpoint-postgres` — https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint-postgres
- atproto MST spec — https://atproto.com/specs/repository#repo-structure
- `@atproto/repo` (TypeScript MST + CAR) — https://github.com/bluesky-social/atproto/tree/main/packages/repo
- IPFS / IPLD CAR spec — https://ipld.io/specs/transport/car/carv1/
- Base L2 (Coinbase) — https://docs.base.org/
- DID Web spec — https://w3c-ccg.github.io/did-method-web/
- `CLAUDE.md` (repo root) — operating entity identity, monorepo layout
- `90-docs/CLAUDE.md` (this repo) — docs system rules
- ADR-2605170900 — this repo as canonical ADR home (depends_on)
- ADR-2605172000 — RW-free substrate (depends_on; the rule that forced this revise)
- ADR-2605172100 — payments + substrate-via-SDK boundary (depends_on)
- ADR-2605152100 — etzhayyim org boundary (cross-repo)
- ADR-2605080600 — LangGraph Server + Granian runtime (sets server runtime context)
- ADR-2605082000 — LangGraph graph-as-data (cell graph schema heritage)
- ADR-2605091300 — Bonsai Cultivar (organism metaphor)
- ADR-2605092000 — Ecosystem-as-Model FP8 substrate (large-blob CID consumer)
- ADR-2605091400 — MCP-as-Cell-Membrane / Lexicon dual-wire (explains why MST is a "cell membrane" concern)
- ADR-2605111300 — PDS-to-Pod Bun container (PDS infra reference for future bridge)
