---
id: adr-2605191655-mst-projector-phase2-design
title: "ADR-2605191655: mst-projector Phase 2 — true MST root + CAR emission"
status: proposed
doc_type: adr
topic: mst-projector-phase2-design
authoritative: true
last_verified: 2026-05-19
priority: 7.5
axis: architecture
weight: 0.75
priority_note: "Locks the upgrade path from Phase 1 counter-derived snapshot hash to a true AT-Protocol MST root + CAR file. Required before downstream consumers (anchor-cron, app readers) can claim third-party verifiability."
authoritative_for:
  - mst-projector Phase 2 implementation contract
  - lexicon migration `snapshotHash` → `rootCid` for `com.etzhayyim.substrate.shardSnapshot`
  - emit format upgrade JSON manifest → CAR file
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605191358-yoro-murakumo-kotoba-rewrite-map
  - 2605191648-substrate-boundary-lefthook
related:
  - 50-infra/mst-projector/
  - 50-infra/ipfs-pinner/
  - 50-infra/anchor-cron/
supersedes: []
superseded_by: []
---

# ADR-2605191655: mst-projector Phase 2 — true MST root + CAR emission

**Status**: proposed
**Date**: 2026-05-19
**Deciders**: Jun Kawasaki

# Context

ADR-2605191358 step 5 shipped as Phase 1 in PR #65 (commit `65f495cd`):

| File | Phase 1 |
|---|---|
| `firehose.ts` | real WS subscriber, CBOR frame decode via `cborg`, cursor persistence, backoff reconnect |
| `mst.ts` | per-shard ordered record list; `currentRoot()` returns `sha256-<hex>` of canonical JSON |
| `shard.ts` | counter + wall-clock `shouldFlush()`; `flushShard()` writes JSON manifest |
| `emit.ts` | optional Kubo IPFS pin; publishes `com.etzhayyim.substrate.shardSnapshot` via `@atproto/api createRecord` |

Phase 1 unblocks step 4 (yoro UI kagami-store) by giving consumers a stable CID per shard flush, but two properties are deferred:

1. **Cross-projector consensus**. The Phase 1 `snapshotHash` is a sha-256 of the projector's local serialisation. Two independent projectors that ingest the same firehose ops in the same order will *also* produce the same hash, but only because both speak the same canonical-JSON format. A future projector implementation in a different language would need to re-derive the same canonical-JSON shape verbatim to reach the same hash. That is not the spec contract; it is an implementation accident.

2. **Self-contained proof artefact**. The JSON manifest stores the per-event tuple (rkey, recordCid, op, seq, did, tsMs) but not the record bodies. Downstream consumers that want to verify a record at a given CID against the snapshot still need to fetch the record from a PDS. A CAR file packing the MST root *and* the leaf blocks gives anyone the data they need offline.

Phase 2 lifts both deferrals by using the AT Protocol MST and CAR format (per repo spec).

# Decision

Phase 2 swaps:

| Component | Phase 1 | Phase 2 |
|---|---|---|
| Tree | per-shard ordered list | `@atproto/repo` MST with base32 collection-prefixed keys, dag-cbor leaves |
| Root identifier | `sha256-<hex>` of canonical JSON | CID v1 (dag-cbor) of the MST root node |
| Flush artefact | JSON manifest with record list | CAR v1 file containing root + all leaf blocks |
| Record CBOR | not captured (op metadata only) | extracted from `body.blocks` (the CAR carried in each firehose frame) |
| Reconstruction on restart | cold start; re-ingest from cursor | warm start by reading the most-recent CAR per shard from `dataDir` |

## Lexicon migration

`com.etzhayyim.substrate.shardSnapshot` was deliberately authored in Phase 1 with both fields:

```json
"snapshotHash": { "type": "string", "description": "Phase 1: …. Phase 2: dropped …" },
"snapshotCid":  { "type": "string", "description": "IPFS CID (v1) of the manifest blob. … required in Phase 2." }
```

Phase 2 evolves the lexicon as follows (separate small PR, not bundled with the code change):

1. New optional field `rootCid` (string) — the MST root CID. The new authoritative field.
2. `snapshotCid` becomes **required** and points at the **CAR file** (not the JSON manifest).
3. `snapshotHash` becomes **deprecated** (kept as optional for one-grace-period; readers MAY accept either).
4. New optional field `phase` increments to `2`. Readers MUST treat absence as `1`.

After the grace period (≥ 4 weeks of Phase 2 production emission), `snapshotHash` is dropped in a follow-up cleanup ADR.

## Wire format

CAR v1 (`application/vnd.ipld.car`) with one root CID equal to the MST root, followed by all reachable leaf and intermediate blocks. Bookkeeping fields go in the AT record:

```jsonc
{
  "$type": "com.etzhayyim.substrate.shardSnapshot",
  "shardKey": "com.etzhayyim.murakumo.inferenceJobEvent",
  "phase": 2,
  "firstSeq": "...",
  "lastSeq": "...",
  "recordCount": 1234,
  "rootCid": "bafyrei...",        // MST root, dag-cbor
  "snapshotCid": "bafkrei...",     // CAR file pinned to IPFS
  "byteSize": 987654,              // size of the CAR
  "flushedAt": "2026-05-19T07:49:56Z"
}
```

## Reconstruction protocol

On startup:

1. For each shard directory under `dataDir`, find the most-recent CAR file.
2. Read its root CID; load the CAR via `@atproto/repo`'s `MemoryBlockstore` + `MST.load(rootCid)`.
3. Set the per-shard cursor to the `lastSeq` recorded in the matching AT record.
4. Resume firehose from `min(per-shard lastSeq, top-level cursor file)`. Any duplicate ops between `lastSeq` and the firehose resume point are idempotent under MST (the same record CID inserts at the same key).

This eliminates the Phase 1 "cold start" gap: a freshly restarted projector reaches the same state any other projector at the same firehose seq would reach.

## Cross-projector consensus claim

After Phase 2 lands, the following property holds: any two projectors that consume the same firehose between (start_seq, end_seq) with the same `ETZ_PROJECTOR_COLLECTIONS` configuration emit the **same `rootCid`** for the same shard at the same flush boundary. Mismatched rootCids → exactly one of the projectors is wrong; the AT record audit trail lets the operator identify which.

`anchor-cron` uses this property when batching shard roots into the Base L2 anchor contract: it aggregates only shard roots that have ≥ N independent projector emissions agreeing on the same `rootCid` (N is a tunable; default 1 during single-replica operation, ≥ 2 once multi-replica deploys).

# Consequences

**Positive**:

- Third-party verifiability: anyone with a CAR file + AT record can independently re-derive `rootCid` and confirm the snapshot.
- Multi-projector consensus is straightforward (compare rootCids at the same firehose seq).
- `anchor-cron` gains a sound input.
- `yoro` kagami-store rewrite (step 4 of ADR-2605191358) can consume CAR files directly via IPFS and skip the AT-record indirection for hot paths.

**Negative / costs**:

- Adds `@atproto/repo` runtime dependency (already in `package.json` from the scaffold; not new).
- CAR files are larger than JSON manifests by a constant factor (dag-cbor headers per block). For sustained high-write shards this matters for IPFS storage budget. Mitigation: tune `ETZ_PROJECTOR_FLUSH_RECORDS` upward.
- Memory pressure: in-memory MST per shard. AT Protocol MSTs are bucketed to keep arity bounded, but a long-running shard with millions of entries needs page-eviction. Phase 2.1 follow-up: paginated MST loading from CAR on demand.

**Required follow-ups**:

- Lexicon migration PR (`com.etzhayyim.substrate.shardSnapshot` v2 fields).
- `anchor-cron` consumer update — switch from `snapshotHash` to `rootCid`.
- `ipfs-pinner` consumer update — pin CAR files (`application/vnd.ipld.car`) instead of JSON manifests.
- Operational ADR for multi-replica deploy (consensus rule for `anchor-cron`).

# Alternatives Considered

**A. Keep counter-based hashes; rely on external verifier service for consensus.**
Rejected. External verifier reintroduces a trust dependency — exactly what ADR-2605172000 forbids.

**B. CARv2 instead of CARv1.**
Rejected for Phase 2. CARv2 adds an index for fast random access, useful for very large CARs, but introduces a second on-disk format. CARv1 is sufficient for shard-sized payloads (target: ≤ 10 MB per CAR). Revisit if shards routinely exceed 100 MB.

**C. Skip CAR; pin individual leaf blocks separately.**
Rejected. Per-block pinning multiplies IPFS API calls per flush by O(records). CAR groups the entire snapshot into one upload, one CID, one pin operation. Atomicity matters for snapshot semantics.

**D. Use IPLD `dag-jose` (signed snapshots) instead of plain dag-cbor.**
Deferred. Signing adds a useful third-party verification path ("this snapshot was emitted by the projector whose key signs it"), but the AT record already carries the projector's DID and the createRecord signature serves the same purpose. Revisit when multi-projector consensus matters more.

# References

- ADR-2605171800 (LangGraph Pregel → MST → IPFS → L2 anchor pipeline — Phase 2 closes Stage 3)
- ADR-2605172000 (kotoba hard rule)
- ADR-2605172100 (substrate-client allowlist — `50-infra/*` is allowed to import `@atproto/repo` directly)
- ADR-2605191358 (yoro/murakumo kotoba rewrite map — step 5 = mst-projector; step 4 yoro UI depends on Phase 2 CAR pinning)
- ADR-2605191648 (substrate-boundary lefthook — note: mst-projector path is allowlisted for raw `@atproto/repo` import)
- `50-infra/mst-projector/` (Phase 1 implementation; this ADR's target)
- AT Protocol repo spec: https://atproto.com/specs/repository
