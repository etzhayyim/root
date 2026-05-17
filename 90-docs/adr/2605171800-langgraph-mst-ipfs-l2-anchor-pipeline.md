---
id: adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
title: "ADR-2605171800: Artificial Organism Ecosystem — LangGraph Pregel → PostgresSaver → atproto MST → IPFS → Base L2 anchor pipeline"
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
  - artificial organism checkpoint pipeline (Pregel → Postgres → MST → IPFS → L2)
  - LangGraph PostgresSaver usage convention for organism cells
  - MST projection schema (atproto-compatible, standalone — no PDS coupling)
  - L2 anchor target (Base) and batching semantics
  - IPFS pinning responsibility split
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
related:
  - https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605080600-langgraph-server-granian-l3-runtime.md
  - https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605082000-langgraph-graph-definition-as-data.md
  - https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605091300-bonsai-cultivar-layer-above-myco-yeast.md
  - https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605092000-ecosystem-as-model-unified-multimodal-fp8-vector-substrate.md
  - https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion.md
  - https://github.com/gftdcojp/ai-gftd-apps-gftdcojp/blob/main/90-docs/adr/2605111300-pds-to-pod-bun-container.md
supersedes: []
superseded_by: []
---

# ADR-2605171800: Artificial Organism Ecosystem — LangGraph Pregel → PostgresSaver → atproto MST → IPFS → Base L2 anchor pipeline

**Status**: proposed
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

# Context

`20-actors/magatama` hosts the Pregel framework that runs **artificial organism cells**: LangGraph-driven actor processes whose state evolves over BSP super-steps. The Bonsai Cultivar series (ADR-2605091300, ADR-2605092000, ADR-2605092100, ADR-2605092200) frames these cells as a living ecosystem — each cell has metabolism, lineage, fission, and a measurable phenotype.

For that metaphor to hold up in production, every cell's state must be:

1. **Durable** — survives crashes / migrations / scale-down. LangGraph already solves this with `PostgresSaver` (the canonical checkpoint saver from `langgraph-checkpoint-postgres`).
2. **Replayable** — any past super-step can be reconstructed deterministically.
3. **Verifiable** — a third party (auditor, peer cell, off-chain observer) can confirm a given state existed at a given step without trusting our infrastructure.
4. **Content-addressed** — large blobs (LoRA weights, embedding tensors, observation buffers, tool outputs) live by hash, not by mutable pointer.
5. **Finalizable** — at coarse intervals, a checkpoint root is anchored on-chain so the chain of state has a public, immutable history.

Plain `PostgresSaver` satisfies (1) and (2) only. The remaining three properties are what this ADR adds.

## Why MST, IPFS, and an L2 — not just Postgres + signatures?

| Property | Postgres alone | + signed Postgres | + MST + IPFS + L2 anchor |
|---|---|---|---|
| Durable | ✅ | ✅ | ✅ |
| Replayable | ✅ | ✅ | ✅ |
| Verifiable by third party | ❌ (trust DB owner) | ⚠️ (trust signing key custody) | ✅ (Merkle proof against on-chain root) |
| Content-addressed | ❌ | ❌ | ✅ |
| Public, immutable history | ❌ | ❌ | ✅ |
| Federable with atproto ecosystem | ❌ | ❌ | ✅ (atproto-shaped MST + CAR) |
| Cell can migrate between hosts without coordination | ⚠️ | ⚠️ | ✅ (IPFS-addressed state, anchor as ground truth) |

The MST + IPFS + L2 trio is also exactly the shape atproto uses for its repo (MST → CAR → optional anchor). Adopting an **atproto-compatible MST projection** means each organism cell is automatically compatible with atproto tooling (`@atproto/repo`, CAR readers, MST verifiers, ipld libraries), which the religious-corp open ecosystem already uses (`10-protocol/at-client`, `50-infra/k8s/atproto-pds`, `60-apps/ai-gftd-project-atproto`).

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

Adopt the following five-stage pipeline for every magatama organism cell that needs verifiable durable state. The pipeline is **append-only**: each stage adds artifacts; nothing is overwritten.

```
┌─────────────────────────────────────────────────────────────────────┐
│  LangGraph Pregel super-step                                        │
│  (cell.invoke / cell.stream — BSP boundaries)                       │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ checkpoint(t)
┌─────────────────────────────────────────────────────────────────────┐
│  PostgresSaver (langgraph-checkpoint-postgres, unmodified)          │
│  Tables: checkpoints, checkpoint_writes, checkpoint_blobs            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ async projection (LISTEN/NOTIFY OR cron)
┌─────────────────────────────────────────────────────────────────────┐
│  MST projector (atproto-shaped, standalone)                         │
│  Reads checkpoint row → builds atproto MST → writes CAR file        │
│  Records (checkpoint_id, mst_root_cid, car_size) into side-table    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ pin
┌─────────────────────────────────────────────────────────────────────┐
│  IPFS                                                                │
│  CAR pinned to local node + remote pinning service                  │
│  Large blobs (>blob_inline_threshold) deduplicated by CID            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ batched anchor (configurable cadence)
┌─────────────────────────────────────────────────────────────────────┐
│  Base L2 — CheckpointAnchor.sol                                     │
│  emit Anchored(did, mst_root_cid, checkpoint_id, ts)                │
│  Side-table records tx_hash, block, log_index                       │
└─────────────────────────────────────────────────────────────────────┘
```

Each stage is independently replayable from the previous stage's artifacts. The chain of cryptographic links is:

```
state(t)  ─sha256─▶  postgres checkpoint row
                              │
                              ▼
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

## Stage 1 — LangGraph Pregel runtime (host: `20-actors/magatama`)

Unchanged from existing `magatama` host. Each cell is a LangGraph graph constructed with the magatama host SDK. Super-step boundaries are defined by LangGraph's normal `interrupt_after` / `interrupt_before` semantics and by the cell's BSP scheduler.

**Convention**: every cell graph builds with `checkpointer=PostgresSaver(...)`. No custom saver subclass. (See § "Alternatives Considered" → C.)

## Stage 2 — PostgresSaver (plain, from `langgraph-checkpoint-postgres`)

Use upstream `langgraph-checkpoint-postgres` as-is. Apply its migrations to the organism Postgres schema. Configure connection per cell or per cell-cohort.

Add **one side-table** owned by this ADR, not by upstream:

```sql
-- 50-infra/mst-anchor/migrations/0001_checkpoint_anchor_sidecar.sql
CREATE TABLE checkpoint_anchor_sidecar (
  -- foreign key into upstream PostgresSaver checkpoints table
  thread_id           TEXT      NOT NULL,
  checkpoint_ns       TEXT      NOT NULL DEFAULT '',
  checkpoint_id       TEXT      NOT NULL,

  -- MST projection
  mst_root_cid        TEXT,                            -- base32 CIDv1 (sha2-256)
  car_size_bytes      BIGINT,
  car_blob_count      INT,
  mst_projected_at    TIMESTAMPTZ,

  -- IPFS
  ipfs_pinned_at      TIMESTAMPTZ,
  ipfs_pin_service    TEXT,                            -- 'local' | 'web3-storage' | …
  ipfs_pin_id         TEXT,

  -- L2 anchor (Base)
  anchor_tx_hash      TEXT,                            -- 0x… 32 bytes
  anchor_block_number BIGINT,
  anchor_log_index    INT,
  anchor_chain_id     INT      NOT NULL DEFAULT 8453,  -- Base mainnet
  anchored_at         TIMESTAMPTZ,

  -- Cell identity
  cell_did            TEXT      NOT NULL,              -- did:web:… or did:plc:…

  -- bookkeeping
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

CREATE INDEX idx_anchor_pending_projection
  ON checkpoint_anchor_sidecar (created_at)
  WHERE mst_projected_at IS NULL;

CREATE INDEX idx_anchor_pending_pin
  ON checkpoint_anchor_sidecar (mst_projected_at)
  WHERE ipfs_pinned_at IS NULL AND mst_projected_at IS NOT NULL;

CREATE INDEX idx_anchor_pending_anchor
  ON checkpoint_anchor_sidecar (ipfs_pinned_at)
  WHERE anchor_tx_hash IS NULL AND ipfs_pinned_at IS NOT NULL;

CREATE INDEX idx_anchor_by_cell
  ON checkpoint_anchor_sidecar (cell_did, anchored_at);
```

PostgresSaver writes are completed transactionally before any sidecar processing starts. The sidecar table is **strictly downstream**; failure of any later stage does not corrupt LangGraph state.

A Postgres trigger inserts a `checkpoint_anchor_sidecar` row on every new `checkpoints` row and `NOTIFY`s the projector daemon:

```sql
CREATE OR REPLACE FUNCTION fn_checkpoint_inserted() RETURNS trigger AS $$
BEGIN
  INSERT INTO checkpoint_anchor_sidecar (thread_id, checkpoint_ns, checkpoint_id, cell_did)
  VALUES (NEW.thread_id, NEW.checkpoint_ns, NEW.checkpoint_id,
          COALESCE(current_setting('app.cell_did', true), 'did:unknown'))
  ON CONFLICT (thread_id, checkpoint_ns, checkpoint_id) DO NOTHING;
  PERFORM pg_notify('checkpoint_inserted',
    json_build_object('thread_id', NEW.thread_id,
                      'checkpoint_id', NEW.checkpoint_id)::text);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_checkpoint_inserted
  AFTER INSERT ON checkpoints
  FOR EACH ROW EXECUTE FUNCTION fn_checkpoint_inserted();
```

`app.cell_did` is set per session by the magatama host before invoking the graph (`SET LOCAL app.cell_did = 'did:web:…'`). Cells without an explicit DID are tagged `did:unknown` and excluded from anchoring (see § "Cell DID provisioning" below).

## Stage 3 — MST projector (`50-infra/mst-projector`)

A standalone daemon (Node.js, uses `@atproto/repo` from npm) that:

1. Subscribes to `pg_notify('checkpoint_inserted', …)`.
2. On each notification, loads the checkpoint row (`checkpoints` + `checkpoint_writes` + `checkpoint_blobs`).
3. **Projects** the checkpoint to an atproto MST. Projection rules:
   - MST key namespace: `magatama.cell.{cell_did_suffix}/checkpoint/{checkpoint_id}`.
   - Each top-level LangGraph state key becomes a record under `magatama.cell.{…}/state/{key}`.
   - LangGraph channel writes (the per-step delta) go under `magatama.cell.{…}/channel/{step}/{channel}`.
   - Records >`blob_inline_threshold` bytes (default 16 KiB) become **separate blobs**, referenced by CID in the MST record. Below threshold, inlined as record content.
4. Serializes the MST to **CAR v1** with deterministic block ordering (so the same logical state produces the same CID).
5. Computes the MST **root CID** and writes it back into `checkpoint_anchor_sidecar.mst_root_cid` along with `car_size_bytes`, `car_blob_count`, `mst_projected_at`.
6. Hands the CAR to Stage 4 (IPFS).

Projection is **pure**: same checkpoint row → same MST root CID, bit-for-bit. This is how third parties verify replay.

## Stage 4 — IPFS pinning (`50-infra/ipfs-pinner`, or service of choice)

The projector daemon pushes the CAR to:

1. **Local IPFS node** (Kubo or Helia, deployed in `50-infra/ipfs/` — currently absent; to be scaffolded in a follow-up).
2. **Remote pinning service** (configurable: web3.storage, Filebase, or Cloudflare R2 with IPFS gateway). At least one remote pin is required for durability.

On successful pin, the daemon writes `ipfs_pinned_at`, `ipfs_pin_service`, `ipfs_pin_id` to the sidecar table.

Large blobs referenced from MST records are pinned **independently** by CID (deduplication: identical embeddings or LoRA weights pinned once across all cells).

## Stage 5 — Base L2 anchor (`50-infra/l2-anchor-contract` + `50-infra/anchor-cron`)

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

1. Selects all sidecar rows with `ipfs_pinned_at IS NOT NULL AND anchor_tx_hash IS NULL`, grouped by cell DID, up to a batch cap (default 100 rows per tx).
2. Constructs `anchorBatch(...)` calldata.
3. Signs with the **organism anchor key** (separate from `did:web:etzhayyim.com` controller key; this is a hot key funded with Base ETH).
4. Submits to Base; waits for 1 confirmation; writes `anchor_tx_hash`, `anchor_block_number`, `anchor_log_index`, `anchored_at` back to the sidecar rows in a single Postgres tx.
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
| PostgresSaver write fails | LangGraph treats checkpoint as not persisted; retries per LangGraph semantics. Sidecar not affected. | None needed (upstream LangGraph behavior). |
| Trigger / NOTIFY fails | Sidecar row not created. | Reconciliation job (hourly): scan `checkpoints` LEFT JOIN sidecar WHERE sidecar.checkpoint_id IS NULL, backfill. |
| MST projection daemon down | Sidecar rows accumulate with `mst_projected_at IS NULL`. | Daemon recovery; index `idx_anchor_pending_projection` makes the backlog cheap to scan. |
| IPFS pin fails | `ipfs_pinned_at` stays NULL; anchor blocked for this row. | Pinner daemon retries with exponential backoff; pin to alternate service if primary down. |
| Anchor tx reverts / underprices | `anchor_tx_hash` stays NULL; row eligible for next batch. | Anchor-cron retries with re-priced gas; circuit breaker if RPC unreachable. |
| Base RPC down | Anchor-cron pauses; sidecar grows. | Self-heals when RPC recovers; backlog auto-drains via index. |
| Anchor key compromised | Attacker can post arbitrary `Anchored` events under our DID. | Rotate the key in the DID document; peers/verifiers reject anchors with old key. The actual cell state in Postgres+IPFS is unaffected — only the *public claim* layer is impacted. |
| MST projection daemon bug → wrong CID | Anchored CID points at corrupted CAR. | Anchors are append-only logs; we cannot un-anchor. Issue a `corrupted=true` follow-up anchor referencing the bad one + the corrected CID. Verifiers prefer latest non-corrupted anchor per (did, checkpoint_id). |

## Repository layout (target — not built in this ADR)

```
20-actors/magatama/
  hosts/                    # existing — magatama Pregel host
  checkpoint-mst/           # NEW — host-side glue: SET LOCAL app.cell_did, etc.

50-infra/
  mst-projector/            # NEW — Node.js daemon, @atproto/repo + pg LISTEN
  ipfs-pinner/              # NEW — wraps Kubo/Helia + remote pinning client
  l2-anchor-contract/       # NEW — foundry project, CheckpointAnchor.sol
  anchor-cron/              # NEW — TS service: batch + viem + Base
  ipfs/                     # currently MISSING from CLAUDE.md — to be scaffolded
                            #   (Kubo node deployment manifests)

60-apps/
  organism-demo/            # NEW — single-cell PoC consuming the pipeline
```

The actual scaffolding of these directories is out of scope for this ADR (per scope decision: ADR-only). A follow-up implementation ADR or task will land them.

# Consequences

## 正の効果

- **Third-party verifiable organism state.** Auditors, peer cells, external researchers can confirm "cell X had state Y at checkpoint Z" with only public artifacts. This is the foundation for the religious-corp public-interest claim that "open" means open-in-the-strong-sense.
- **Cell migration is cheap.** Move a cell between hosts → ship its DID + IPFS pins; new host re-binds to its Postgres or rebuilds Postgres state from the CAR. No coordination with central authority.
- **atproto ecosystem compatibility.** Standard tooling (`@atproto/repo`, CAR readers, IPLD libs) reads organism state. Bridge to PDS publication is a future ADR away.
- **Composable with Bonsai Cultivar metaphor** (ADR-2605091300). Cells have lineage (anchor chain), metabolism (rate of MST growth), and reproduction (fission = copy CAR + fork DID). All measurable from public artifacts.
- **No vendor lock-in.** Postgres, IPFS, Base, and atproto MST are all open standards / open-source. Anchor contract is 50 lines of permissive-license Solidity.
- **Failure isolation.** PostgresSaver is the only stage in the cell's hot path. MST/IPFS/L2 are async; their failures degrade verifiability, not cell operation.

## 負の効果 / コスト

- **Operational surface area grows by 4 services**: MST projector, IPFS pinner (+ IPFS node), anchor cron, and the deployed Base contract. Each needs monitoring, key custody, and a runbook.
- **L2 anchor cost.** At 60s cadence per cell with batching, rough order-of-magnitude is $0.01–$0.10 per cell per day on Base (calldata-dominated). Cheap individually, but linear in cell count. For 10⁴ cells: ~$100–$1000/day. Mitigation: longer batch periods, IPFS-as-default + opt-in anchor per cohort, future move to a data-availability layer if scale demands it.
- **Hot anchor key custody.** A wallet funded with Base ETH that signs anchor txs must be protected. Mitigation: HSM or threshold signature; rotation procedure in the DID document.
- **Standalone MST cannot federate via PDS-relay.** Cells are not visible in atproto firehoses unless we add a publishing surface. Acceptable for v1 (verifiability ≠ federation); future ADR can add a PDS export.
- **MST projection determinism is load-bearing.** A bug that changes block ordering or encoding silently breaks reproducibility. Mitigation: golden-CAR tests in CI, snapshot tests across `@atproto/repo` upgrades.
- **Postgres trigger adds load** to checkpoint writes. NOTIFY is cheap but adds ~10–50µs per checkpoint. Negligible at expected cell rates (<10 Hz/cell) but worth measuring under load.
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

This ADR is the **contract**, not the build. Rollout is staged:

- [ ] **Phase 0 — this ADR (now).** Contract is published.
- [ ] **Phase 1 — reference impl (follow-up).** Scaffold the 4 new infra packages + 1 PoC app under `60-apps/organism-demo/`. Single cell, single thread, end-to-end verifiable on Base sepolia.
- [ ] **Phase 2 — magatama host integration.** Magatama Pregel host calls `SET LOCAL app.cell_did` on every cell session start.
- [ ] **Phase 3 — Base mainnet deploy.** Deploy `CheckpointAnchor.sol` on Base mainnet. Address recorded in `deps.toml` under `[platform.l2_anchor]`. Wallet funded.
- [ ] **Phase 4 — first production cell.** A real cell from an `60-apps/ai-gftd-project-open-*` project opts into the pipeline. Monitor cost + latency for one week.
- [ ] **Phase 5 — IPFS infra scaffolded.** `50-infra/ipfs/` Kubo deployment (currently missing from layout in `CLAUDE.md`).
- [ ] **Phase 6 — `lefthook.yml` `adr-validate` hook** ensures any ADR claiming `authoritative_for` overlapping this one is properly chained via `supersedes`.

# Alternatives Considered

## A. Postgres-only (no MST, no IPFS, no anchor)

LangGraph + PostgresSaver, done. Cells are durable and replayable.

却下理由: fails third-party verifiability, content-addressability, and public history. The organism metaphor's "open" property collapses to "trust the operator." This is the same failure mode that motivates ADR-2605152100's principal/vendor boundary — we want the open ecosystem to be *demonstrably* open, not just nominally so.

## B. Atproto PDS as canonical store

`50-infra/k8s/atproto-pds` is already deployed (per CLAUDE.md). Use it as the canonical store; each cell is an atproto repo; checkpoints are repo commits.

却下理由: couples cell cadence to PDS commit rate, forces every cell to look like an atproto identity (heavyweight for short-lived cells), and bakes federation policy into the data layer. The MST is the useful primitive, not the PDS; we adopt the primitive without the package. PDS publication can be added later as a publishing surface (Phase 6+).

## C. Custom PostgresSaver subclass that emits MST inline

Subclass `PostgresSaver`, override `put()` to project + pin + (optionally) anchor in the same transaction.

却下理由: tight coupling between cell hot path and three async dependencies. A slow IPFS or Base RPC stalls every super-step. Even with retries-and-fallback, debugging becomes hard. The chosen design (plain saver + async sidecar) preserves LangGraph's stability and keeps verifiability fully decoupled.

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
- ADR-2605152100 — etzhayyim org boundary (vendor; cross-repo)
- ADR-2605080600 — LangGraph Server + Granian runtime (vendor; sets server runtime context)
- ADR-2605082000 — LangGraph graph-as-data (vendor; cell graph schema heritage)
- ADR-2605091300 — Bonsai Cultivar (vendor; organism metaphor)
- ADR-2605092000 — Ecosystem-as-Model FP8 substrate (vendor; large-blob CID consumer)
- ADR-2605091400 — MCP-as-Cell-Membrane / Lexicon dual-wire (vendor; explains why MST is a "cell membrane" concern)
- ADR-2605111300 — PDS-to-Pod Bun container (vendor; PDS infra reference for future bridge)
