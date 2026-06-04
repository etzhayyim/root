---
id: adr-2606041151-kotoba-commitdag-as-wal-and-incremental-query-tier
title: "ADR-2606041151: kotoba canonical-tier hardening — CommitDag-as-WAL (Journal demotion) + incremental MaterializedView query tier"
status: proposed
doc_type: adr
topic: kotoba-commitdag-as-wal-and-incremental-query-tier
authoritative: true
last_verified: 2026-06-04
priority: 6.5
axis: architecture
weight: 0.66
priority_note: "Removes the structurally-redundant WAL layer and makes Datomic/Datalog query genuinely first-tier"
authoritative_for:
  - 40-engine/kotoba (design intent)
depends_on:
  - "2605262130"
  - "2605312345"
related:
  - "2606041130"
  - "2605240001"
supersedes: []
superseded_by: []
---

# ADR-2606041151: kotoba canonical-tier hardening — CommitDag-as-WAL + incremental MaterializedView query tier

**Status**: proposed
**Date**: 2026-06-04
**Deciders**: Jun Kawasaki

# Context

A structural analysis of the kotoba write/query path (source-grounded, 2026-06-04)
surfaced two findings about layers that are *present* but not *structurally
necessary* — and one layer (Datomic Datalog query) that is *intended* first-tier
but not realised as such.

## Finding 1 — in-memory Arrangement + Journal WAL are optimisation/deferral artifacts

The canonical state is the **Datom log**, materialised as content-addressed
ProllyTree indexes (EAVT/AEVT/AVET/VAET) + the **CommitDag** (ADR-2605312345).
Everything is reconstructible from the committed ProllyTrees.

- **Hot Arrangement** — the authors' own note states *"in-memory Arrangement is
  only an optimisation"* (`40-engine/kotoba/CLAUDE.md`, "Datalog over IPFS-backed
  cold storage"). It is (a) the write-side accumulator `commit()` sorts into the 4
  ProllyTrees and (b) an ns–µs read cache. Both are performance, not correctness.
- **Journal WAL** — every `assert` calls `publish_legacy_quad_assert`, which
  publishes to **4 topics (spo/pso/pos/osp)**, each a `BlockStore.put`
  (`crates/kotoba-graph/src/quad_store.rs:232-260`). A single quad is therefore
  written to the WAL (4 journal blocks) **and** later to the ProllyTree leaves at
  `commit()` — **double-write + write-amplification**. After commit + checkpoint
  the WAL blocks are garbage.
- Because the only durable block backend today is **Kubo-over-HTTP** (the embedded
  `sled` store was removed 2026-05-26 — the kotoba-store crate now ships only
  `memory_store` (volatile) + `kubo_store` (HTTP) + wrappers), every WAL write pays
  an HTTP round-trip. Measured cost: **~30 s WAL replay for 7 entries** against
  Kubo; the authors' own recommendation is *"split: Journal WAL on local
  filesystem (fast replay), Kubo for durable archival export of sealed commits
  only"* (`CLAUDE.md`, "Persistence E2E vs real Kubo").

**Key insight — WAL-necessity is independent of IPFS locality.** A separate WAL
exists only to cover the *time gap* between *write-accepted* and
*write-committed-into-a-ProllyTree*. That gap is created by **batching/deferring
commits**, not by IPFS being remote. The `CommitDag` — a chain of immutable,
content-addressed, parent-linked `Commit` blocks — **is already a write-ahead log
by construction** (the git/Datomic model: the commit log *is* the WAL). A second
Journal WAL is pure redundancy *unless* commits are deferred.

So: *"if kotoba holds a local IPFS, is synchronous commit unnecessary?"* — local
IPFS makes commit **cheap**, but it does not by itself remove the WAL. The WAL
disappears only when commits are **synchronous / micro-batched** (each accepted
write is immediately a CommitDag commit) — and that is *enabled* by a fast local
block store. Local IPFS is necessary-but-not-sufficient; synchronous commit is the
act that collapses the WAL into "commit blocks + an atomic head-ref update."

## Finding 2 — Datomic Datalog query is intended first-tier but is a from-scratch evaluator

By intent the README states *"Datomic/Datalog primary, SPARQL auxiliary."* The
4-index model is genuinely first-tier *as a data model*. But the Datomic **query
engine** is not first-tier in practice:

- `kg.query` (`crates/kotoba-server/src/kg.rs:1794` → `1859`) calls
  `current_graph_deltas()` then `program.evaluate_delta(&input_deltas)` — it
  **rebuilds the fact base from scratch on every call** (no incremental Δ or
  persisted IDB between requests). Measured: **2.1× slower than the "auxiliary"
  `kg.sparql` cold-BGP path** (36 vs 75 QPS, 2000 entities).
- The one component that would make Datalog first-tier —
  `MaterializedView` ("incrementally maintained Datalog query result",
  `crates/kotoba-kqe/src/mv.rs`) — **exists as a primitive but is unwired into the
  server** (referenced only by its own tests). The CID-MV cache
  (`cold_query_sparql_bgp_cached`) accelerates SPARQL, not Datalog.

Net: the Datomic *indexes* are tier-1 (EAVT point lookup ~180 ns); the Datomic
*Datalog query* is effectively tier-3 (behind hot index-scan and SPARQL-BGP).

# Decision

## A. CommitDag-as-WAL — embedded local block store + micro-batch synchronous commit; demote/remove the Journal WAL

1. **kotoba becomes its own IPFS blockstore + pinner** — re-introduce an
   embedded, durable, in-process block store (direct flatfs/sled/redb — NOT
   Kubo-over-HTTP) as the hot durable tier inside `TieredBlockStore`, and let
   kotoba hold pins itself (a flag in its own store, no `pin/add` RPC). This is
   what *"kotoba holds local IPFS"* must mean: blocks are written to local disk
   directly (µs–ms, fsync), not via an HTTP round-trip to a sidecar daemon.
   `IpfsPinClient` + the block-store abstraction already exist; only the durable
   local backend is missing (the embedded `sled` store was removed 2026-05-26).
   **Efficiency**: this removes the HTTP-RPC hop that today costs
   **142 → 5,222 ingest ent/s (≈35×)** and the **~30 s WAL replay**, and lets the
   B2 cold pin (ADR-2606041130) read blocks directly instead of `block/get` over
   HTTP. Kubo (IPFS network) and B2 become **async export of sealed commits**, off
   the hot write path.
2. **Adopt micro-batch synchronous commit.** Each ingest call (or a short
   time/size window, e.g. ≤N ms / ≤K datoms) immediately runs `apply_batch` →
   new ProllyTree roots → a new `Commit` appended to the `CommitDag`, persisted to
   the embedded store, then an **atomic head-ref update**. The durability boundary
   is the head-ref write (git-ref / Datomic-commit semantics).
3. **The CommitDag is the write-ahead log.** Eliminate the separate per-assert
   Journal WAL as the system of record. Crash recovery = "load the durable head +
   walk commits since the last checkpoint" — already content-addressed, no replay
   of a second log. Optionally retain a **tiny local-FS scratch** for only the
   in-flight micro-batch (sub-second, never IPFS-backed, never authoritative); if
   micro-batches are small enough this scratch can be dropped entirely.
4. **Stop the 4-topic legacy quad fan-out** (`publish_legacy_quad_assert`) on the
   durable path; the Datom-native `pending_datoms` + the committed ProllyTrees are
   sufficient.

This subsumes the user's intuition precisely: local IPFS (embedded store) is the
enabler; micro-batch synchronous commit is what makes the Journal WAL unnecessary.

## B. Wire MaterializedView into the server as the first-tier Datalog query path

1. Register each Datalog program / recurring query as a **persisted
   `MaterializedView`** keyed by `program_cid` (the primitive exists in
   `kotoba-kqe/src/mv.rs`).
2. **Incrementally maintain** each MV: feed every commit's Δ (the engine already
   emits `Delta`s) into the registered MVs via semi-naive incremental update —
   not a from-scratch `evaluate_delta` per request.
3. Persist MV state content-addressed by `(commit_cid, program_cid)` (reuse the
   CID-MV cache pattern already used for SPARQL), so an MV is a durable, shareable,
   addressable Datom-log derivative; a new commit invalidates/advances it.
4. Route `kg.query` to read the maintained MV (hot) and fall back to
   `evaluate_datalog_cold` only on cold miss / first registration. Recursive rules
   (transitive closure) then get IVM instead of full re-evaluation.

This makes "Datomic/Datalog primary" real: the canonical Datom indexes *and* the
Datalog query engine both become first-tier.

## C. (situational) kotoba as a networked IPFS *pin service* for peers — distributed-durability evolution

Decision A makes kotoba its own *local* blockstore/pinner (the high-value, single-
node win). A second, **situational** layer is to run kotoba as a *networked* IPFS
pin **service** so peers replicate to each other natively:

1. Re-enable `kotoba-net` p2p (today **QUIC-only and compile-gated** —
   `--features p2p` is off in the running build) so kotoba serves/fetches blocks
   over **bitswap + Kademlia DHT** directly, and optionally exposes the **IPFS
   Pinning Service API** (`/api/v1/pins`) so other nodes can pin to it.
2. The **donated-node mesh** (ameno / e7m / kotoba pods, ADR-2606012100) then
   replicates sealed commits **peer-to-peer**, making off-host durability **live
   and multi-copy** rather than a periodic backup. The B2 cold pin (ADR-2606041130)
   becomes **one of several replication targets**, not the only off-host copy.
   Charter-clean: this is the storage-donation node class
   (`computeDonationAttestation`), content-addressed, **no server signing key**.

**Cost / when**: a full networked node is heavy (always-on libp2p swarm + DHT +
bitswap + NAT traversal, ADR-2606039000) and kotoba deliberately **removed the
iroh-blobs stack 2026-05-27**, so this means re-adopting a Rust IPFS networking
path. It is **worth it only when multi-node live replication is actually wanted**;
for a single node, Decision A's local store captures ~90% of the efficiency. So C
is gated on the donated mesh being live + `kotoba-net` p2p re-enabled, and it
**supersedes the "periodic B2 pin is the only off-host copy" posture** of
ADR-2606041130, not Decision A.

# Consequences

- **A**: removes WAL write-amplification + the ~30 s Kubo-RTT replay; restart
  becomes a content-addressed head load. Writes get a true local durability floor
  independent of any daemon. Cost: re-introducing an embedded store + commit
  cadence work; per-tx commit overhead bounded by path-copy delta + CAR batching
  (already ms-class). Risk: micro-batch sizing (latency vs block churn) needs
  tuning; head-ref atomicity must be crash-safe.
- **B**: Datalog query stops being a from-scratch evaluator → first-tier
  incremental. Cost: MV registry + memory for maintained views + invalidation
  policy. Risk: unbounded MV set; needs an eviction/budget (reuse
  `BudgetedBlockStore` semantics).
- **C** (situational): turns periodic, single-copy B2 backup into live multi-copy
  peer replication across the donated mesh; off-host durability stops depending on
  one volume + one scheduled job. Cost: re-enabling/owning a networked IPFS stack
  (libp2p swarm, DHT, NAT, GC, provider records) — heavy; gated on the mesh being
  live and only worthwhile for multi-node deployments. Supersedes the B2-only
  off-host posture (ADR-2606041130), not Decision A.
- All three are **design-only** here (kotoba is an upstream submodule); no Charter
  invariant is touched (Datom log remains canonical, no server key — pinning is
  content-addressed, Murakumo-only inference unaffected). Implementation lands
  upstream in `40-engine/kotoba`.

# Alternatives Considered

- **Keep the Journal WAL but move it to local-FS** (the authors' lighter
  recommendation): valid, lower-risk; keeps batched commit + a cheap ephemeral
  WAL. Rejected as the *target* because it preserves two logs and the
  double-write; accepted as a **migration step** toward A.
- **"Local IPFS alone removes the WAL"**: rejected — analysed above; locality
  lowers commit cost but does not remove the deferral gap. Without synchronous /
  micro-batch commit the WAL is still structurally required.
- **Per-write (fully synchronous) commit, no micro-batch**: rejected as default —
  correct but pays a ProllyTree path-copy + block writes per datom; micro-batching
  amortises that while keeping the WAL-free property.
- **Materialise Datalog via the existing SPARQL CID-MV cache**: insufficient — that
  cache memoises whole SPARQL result sets per commit, not *incrementally
  maintained* Datalog derivations; recursive rules still re-run on each new commit.

# References

- 90-docs/adr/2605312345-kotoba-datom-first-class-canonical-state.md
- 90-docs/adr/2605262130-kotoba-storage-substrate-unification.md
- 90-docs/adr/2606041130-kotoba-b2-blockstore-cold-pin.md
- 40-engine/kotoba/CLAUDE.md ("Persistence E2E vs real Kubo", "Datalog over IPFS-backed cold storage", "kg.query vs kg.sparql head-to-head")
- 40-engine/kotoba/crates/kotoba-graph/src/quad_store.rs (assert / publish_legacy_quad_assert / commit)
- 40-engine/kotoba/crates/kotoba-kqe/src/mv.rs (MaterializedView — unwired)
- 40-engine/kotoba/docs/kotoba-canonical-vs-optimization.svg (analysis + A/B)
- 40-engine/kotoba/docs/kotoba-datomic-architecture.svg (current)
