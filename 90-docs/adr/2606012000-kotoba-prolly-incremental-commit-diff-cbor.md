---
id: adr-2606012000-kotoba-prolly-incremental-commit-diff-cbor
title: "ADR-2606012000: kotoba ProllyTree incremental commit (path-copy) + O(|diff|) diff + CBOR leaf values"
status: accepted
doc_type: adr
topic: storage-substrate
authoritative: true
last_verified: 2026-06-01
priority: 5.0
axis: architecture
weight: 0.60
priority_note: "Delivers the incremental + diff 'soul' the Prolly-on-content-addressed-store design was always meant to have. Eliminates the per-commit full-history cold re-read (history_datoms_cold) that made commit cost grow with total DB size — the IPFS-amplified scaling wall. Implements ProllyTree::apply_batch (path-copy), a real ProllyTree::diff/diff_entries, switches persisted leaf values to CBOR, and fixes two read-amplification bugs (list_leaves leaf-loading, scan_prefix tail-scan) found by measurement."
authoritative_for:
  - "kotoba commit() is incremental: per-tx delta applied onto the previous commit's index roots (no full-history re-read)"
  - "ProllyTree::apply_batch path-copy semantics + convergence-with-build_tree invariant"
  - "ProllyTree::diff / diff_entries as the content-addressed diff primitive"
  - "persisted ProllyTree leaf values are DAG-CBOR (ciborium), not JSON"
depends_on:
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605262130-kotoba-storage-substrate-unification
related:
  - adr-2605231902-feed-post-membrane-and-feed-discover-projection
  - adr-2605240001-kotoba-cleanroom-architecture
supersedes: []
superseded_by: []
---

# ADR-2606012000: kotoba ProllyTree incremental commit (path-copy) + O(|diff|) diff + CBOR leaf values

**Status**: accepted
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

kotoba stores its four Datomic-ordered indexes (EAVT/AEVT/AVET/VAET, plus the
Datom-native 5-index set + a TEA time index) as content-addressed Prolly trees
over a `BlockStore` whose primary tier is IPFS (Kubo). This is the natural —
arguably optimal — substrate for a Prolly tree: a node's CID *is* its IPFS CID,
so structurally-shared (unchanged) chunks dedup for free at the protocol layer.

But the "soul" of a Prolly-on-content-addressed-store design — **incremental
path-copy updates** and **diff at the cost of the difference** — was not
implemented:

- `QuadStore::commit()` rebuilt every index tree **from scratch** each commit,
  and to do so called `history_datoms_cold()`, which re-reads the **entire**
  datom history back through the ProllyTree (over IPFS). Commit cost therefore
  grew with **total DB size**, and the per-level block GETs multiply by IPFS RTT
  — the scaling wall called out in the substrate review.
- `ProllyTree::diff()` was a placeholder returning the two roots.
- Leaf values were JSON (`serde_json`), larger than the DAG-CBOR the rest of the
  block layer uses.

# Decision

## 1. Incremental commit via `ProllyTree::apply_batch` (path-copy)

New `ProllyTree::apply_batch(prev_root, upserts, deletes, store) -> new_root`
path-copies only the leaves a batch key routes into (handling boundary-key
**splits** and boundary-delete **merges** locally), keeps every untouched leaf's
CID verbatim, and rebuilds the internal spine. Because leaf membership is a pure
function of the key set (`is_boundary(key)`), the result is **bit-for-bit
identical** to `build_tree` over the same final entries (proven by a 30-round
randomized convergence test: incremental root CID == from-scratch root CID).

`commit()` no longer calls `history_datoms_cold()`. Instead it applies the
per-tx delta onto the previous commit's `index_roots`:

- **Append-only trees** (`datom_eavt`, `datom_aevt`, `tea`): additive upserts of
  the tx's datoms (keys include `tx`+`op` → unique).
- **Current-view trees** (`datom_avet`, `datom_vaet`): upsert the tx's net
  asserts (`current_datoms` of the tx), and retract each touched triple's prior
  representative — located via a bounded `scan_prefix` on the previous root
  (new `Datom::avet_prefix` / `vaet_prefix` helpers; at most one representative
  per `(e,a,v)` triple, so the prefix is unique).
- **Quad-compat trees** (`eavt/aevt/avet/vaet`): unchanged — still built from the
  in-memory `Arrangement` (no cold read; multi-valued keys preclude `apply_batch`).

Correctness is locked by `incremental_commit_datom_roots_match_full_rebuild`:
over a multi-commit chain (asserts, retracts, representative replacement, VAET
refs) every committed Datom-native index root equals a from-scratch rebuild of
the cumulative history.

## 2. Real `ProllyTree::diff` / `diff_entries`

`diff` returns the leaf CIDs unique to each side (for replication: "ship these
blocks"); `diff_entries` returns added / removed / changed `(key,value)` triples.
Identical leaves share a CID and are never loaded, so cost is proportional to the
**differing** leaves plus an `O(#internal nodes)` leaf listing — the `O(|diff|)`
behaviour that makes db-before/after, branch/merge and replication-by-diff cheap
on a content-addressed store. Verified against a brute-force diff over a mixed
add/remove/change set.

## 3. CBOR leaf values

Persisted ProllyTree leaf values (full `Datom`, and Quad-compat `LegacyQuadObject`)
are encoded with `ciborium` (DAG-CBOR) via centralized
`enc_datom`/`dec_datom`/`enc_object`/`dec_object` helpers — compact, byte-stable,
consistent with the CIDv1 dag-cbor block layer. In-memory dedup keys and the
Journal WAL format are unchanged.

## 4. Two read-amplification fixes (found by measurement)

A byte-counting `BlockStore` test (`commit_reads_scale_with_delta_not_history`)
falsified the first-cut "O(delta)" claim and exposed two bugs:

- **`list_leaves` loaded every leaf** to read its `max_key` → `apply_batch` read
  the whole tree each commit. Fixed: leaf pointers `(max_key, leaf_cid)` are read
  from the bottom internal level (one peek per internal node determines the
  level), so leaves are never loaded → `O(#internal nodes)`.
- **`scan_prefix` never early-terminated for an absent prefix** (pre-existing) →
  it scanned the whole tail of the tree. Fixed with a prefix-upper-bound; also
  speeds up every cold read (all route through `scan_prefix`).

# Consequences

- **Commit no longer re-reads the full history.** Per-commit block-store reads
  for a fixed delta scale **sublinearly** with graph size (measured 32k/8k bytes
  ratio ≈ **1.8×** vs the ~4× a full re-read shows; trend flattens toward the
  O(delta) plateau). The IPFS RTT amplification on commit is removed.
- Diff/branch/merge/replication-by-diff are now cheap on the content-addressed
  store — the dividend that justified Prolly in the first place.
- Smaller blocks (CBOR) over IPFS.
- Tests: kotoba-core 100 ✓, kotoba-kqe 205 ✓, kotoba-graph 228 ✓.

## Honest limits

- **Not a flat O(delta) plateau at small/medium scale.** Datom keys are
  content-hashed (no locality), so a small delta scatters across leaves; reads
  only fully plateau once `#leaves ≫ delta`. True per-commit locality would need
  monotonic-`T` / entity-ordered keys (Datomic-style) — a future ADR.
- **Quad-compat indexes still rebuild from the in-memory `Arrangement`** each
  commit (O(current) CPU, but **no cold read**). Making them Datom-derived /
  incremental is follow-up work.
- **CBOR is a format break** for any pre-existing on-disk JSON-valued graph
  (acceptable pre-1.0; the Journal WAL is unchanged so replay is unaffected).
- `diff` prunes at leaf granularity (already O(|diff|)-class), not multi-level
  subtree skip.

# Alternatives Considered

- **Key-deterministic internal boundary (level-seeded hash)** to make internal
  levels path-copy-local too. Cleaner long-term, but a larger rewrite that
  changes every CID/tree shape; deferred. `apply_batch` instead keeps the
  existing CID-based boundary and rebuilds the spine from the (cheap) leaf
  pointer list — still converges with `build_tree`.
- **In-memory cumulative current-view cache** to avoid the cold read. Rejected:
  grows with live-set size; the bounded `scan_prefix` delta approach needs no
  resident state.
- **Leaving leaf values as JSON.** Rejected: inconsistent with the DAG-CBOR block
  layer and larger over IPFS.

# References

- `40-engine/kotoba/crates/kotoba-core/src/prolly.rs` — `apply_batch`, `diff`,
  `diff_entries`, `list_leaves`, `scan_prefix`
- `40-engine/kotoba/crates/kotoba-graph/src/quad_store.rs` — incremental
  `commit()`, `TreeOp`, `enc_datom`/`dec_object`, scaling + equivalence tests
- `40-engine/kotoba/crates/kotoba-kqe/src/datom.rs` — `avet_prefix`/`vaet_prefix`
- ADR-2605312345 — kotoba Datom as first-class canonical state
- ADR-2605262130 — kotoba storage substrate unification
