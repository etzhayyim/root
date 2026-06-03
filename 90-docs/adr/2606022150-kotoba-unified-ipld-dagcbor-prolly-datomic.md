---
id: adr-2606022150-kotoba-unified-ipld-dagcbor-prolly-datomic
title: "ADR-2606022150: kotoba unified substrate — true DAG-CBOR / Prolly / Datomic with the hot index as a derived projection"
status: active
doc_type: adr
topic: kotoba-unified-ipld-substrate
authoritative: true
last_verified: 2026-06-02
priority: 6.5
axis: architecture
weight: 0.75
priority_note: "Removes the dual hot/cold representation and the dag-cbor-in-name-only encoding; makes the canonical Datom log a genuine IPLD DAG."
authoritative_for:
  - kotoba-canonical-block-encoding
  - kotoba-hot-index-derivation
depends_on:
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2606013600-kotoba-wasm-browser-node
related:
  - adr-2605240001-kotoba-cleanroom-architecture
supersedes: []
superseded_by: []
---

# ADR-2606022150: kotoba unified substrate — true DAG-CBOR / Prolly / Datomic, hot index as derived projection

**Status**: active — design SSoT; implementation phased (P1 landed, P2/P3 in progress)
**Date**: 2026-06-02
**Deciders**: Jun Kawasaki

# Context

ADR-2605312345 makes the kotoba **Datom log the first-class canonical state**:
content-addressed EAVT/AEVT/AVET/VAET covering indexes materialised as **Prolly
Trees** over an IPLD block store, CIDs labelled `CIDv1 dag-cbor sha2-256`. Reading
the actual `40-engine/kotoba` workspace surfaced two gaps between that stated model
and the code:

**Gap A — the hot path is a second, independently-coded representation.**
`QuadStore.arrangements: DashMap<String, kqe::Arrangement>` is the hot read path,
and `Arrangement` is a hand-rolled family of `HashMap`/`BTreeMap` indexes
(`spo/pso/pos/ocp`) maintained *in parallel* with the cold Prolly Trees and tracked
by a `hot_covers_all` superset flag. It is not a cache *derived* from the canonical
Datoms — it is a parallel structure with its own types and quirks. Those quirks are
real defects: `Arrangement::insert_value` is a plain `push` with **no dedup**, so
re-loading overlapping state multiplies rows (hand-patched in `kotoba-wasm` per
ADR-2606013600, but the root cause is in `kqe`), and snapshot export keyed entities
by a `Debug` string rather than a stable CID. A single canonical structure with a
*derived* hot index would not have these.

**Gap B — the blocks are "dag-cbor" in name only.** `prolly.rs` serialises nodes
with **`ciborium`** (generic CBOR) and derives the CID as `sha2-256(cbor_bytes)`.
The CID *codec byte* is `0x71` (dag-cbor) and the multihash is sha2-256 — but the
**payload is not DAG-CBOR**: child links are encoded as raw `[u8;36]` byte arrays,
**not IPLD CID tag-42 links**, and there is no canonical-encoding guarantee. A
generic IPLD/IPFS tool cannot walk the DAG. The stale comment `// CID =
blake3(node_bytes)` compounds the confusion (the hash is actually sha2-256).

Both gaps are independent. `serde_ipld_dagcbor v0.6.4` (canonical DAG-CBOR, encodes
`cid::Cid` as tag-42 by default) is fetchable; `ipld-core 0.4` and `cid 0.11` are
already in the workspace.

# Decision

Make the **canonical state a genuine IPLD DAG of true DAG-CBOR blocks**, and make
the **hot index a derived projection** of that canonical structure — never a
parallel source of truth.

## D1. True DAG-CBOR Prolly nodes (Gap B)

Prolly-tree nodes are encoded with **canonical DAG-CBOR** and child links are
emitted as **IPLD CID tag-42**:

- Encode/decode via `serde_ipld_dagcbor` (canonical: definite-length, sorted map
  keys, no NaN/Inf). The node CID stays `sha2-256(dag-cbor-bytes)` with codec `0x71`
  — now a *legitimate* dag-cbor CID.
- Links serialise as tag-42 by routing each child `KotobaCid` through
  `::cid::Cid` (via `to_standard_cid` / `from_standard_cid`).
- **Containment**: the change is confined to the Prolly node codec
  (`kotoba-core::prolly`) through a serialization-mirror (`Leaf`/`Internal` with
  `cid::Cid` links). **`KotobaCid`'s global serde is NOT changed** — it is still a
  byte array in commit blocks / server JSON / `StoredDatom`. Widening tag-42 to
  every `KotobaCid` site is a separate, later ADR (much larger blast radius).
- Keys/values use `serde_bytes` so they encode as CBOR byte strings, not arrays.

The boundary function is unchanged (`blake3(key) & MASK`); only node *serialisation*
becomes true DAG-CBOR. The stale `blake3(node_bytes)` comment is corrected.

## D1.1 Canonical index key encoding ≠ block encoding (CRITICAL)

DAG-CBOR is the right **block** encoding but the **wrong** encoding for a range
index's sort keys: its major-type framing, length prefixes and CID tags do not
make `memcmp` equal value order. The Prolly Datomic indexes (EAVT/AEVT/AVET/VAET)
therefore use a **separate, purpose-built ordered binary tuple encoding** — the
classic `[type-tag][order-preserving-value][separator]` layout — with four
non-negotiable properties: **canonical** (one encoding per value), **type-tagged**
(types in disjoint key ranges; a string never compares against a number),
**bytewise-sortable == semantically-sortable**, and **stable across
implementations**.

The traps this fixes (each was a real defect or risk in the pre-existing code):

- **signed `i64`**: encode with a **sign-bit flip** (`n ^ 0x8000…`), not raw
  `to_be_bytes()` — otherwise `-1` (`0xFF…`) sorts *after* `+1`. The hot path was
  worse: `value_key` used `n.to_string()`, the textbook `"100" < "20"` bug.
- **`f64`/`f32`**: encode with the **total-order transform** (negatives bit-flipped
  and moved below positives; `-0.0` folded to `+0.0`), not raw IEEE-754 bits.
- **text/bytes**: **escape `0x00 → 0x00 0xFF`, terminate `0x00 0x00`** so an
  embedded NUL cannot forge a field boundary (prefix-bleed). Fixed-width fields
  (CID 36 B, bool 1 B) need no terminator.

This lives in `kotoba-kqe::keycodec` as the **single source of truth**; both the
cold Prolly keys (`datom::*_key`) and the hot AVET index route through it, so hot
and cold order identically — a precondition for D2's derived-projection equality.
Block bytes stay DAG-CBOR (D1); sort keys are this codec. The two are deliberately
distinct.

## D2. Hot index = derived projection (Gap A)

The hot `Arrangement` is redefined as a **deterministic projection of the canonical
Datom set**, not a parallel structure:

- One Datom type and one decoded-scalar/value codec across hot and cold; the
  arrangement is rebuildable from `datoms()` and is provably a pure function of the
  Prolly leaves it covers.
- **Dedup is intrinsic**: assertions are keyed by `(resolved-entity-CID, attr,
  value)`; a repeated assert is a no-op (no duplicate `push`). This generalises the
  `kotoba-wasm` fix into `kqe` so every caller — server and browser — inherits it.
- Point reads stay **O(1)** (the index is still an in-memory map); we are removing
  the *divergence* between hot and cold, not the in-memory accelerator. The
  loadtest hot-path numbers (ADR-2605312345 / kotoba CLAUDE.md) are preserved.
- `hot_covers_all` semantics are retained but reframed: the flag asserts the
  projection covers the committed Prolly state; it never lets hot hold facts that
  are not a function of the canonical log.

This is the **"导出キャッシュ化"** decision: hot is a cache *of* the canonical
DAG-CBOR/Prolly/Datomic structure, eliminating the second implementation.

## D3. Browser node on the same Prolly/IPLD path (ADR-2606013600 follow-on)

The deferred P1 item — `DistributedDatomReader` Prolly traversal over
`IdbBlockStore` — is implemented so the **browser uses the identical
IPLD/Prolly/Datomic read path** as the server: hydrate by pulling Prolly blocks,
**CID-verify each block on arrival**, and traverse the four covering trees in-wasm.
The bespoke in-memory `[{e,a,v_edn}]` snapshot (ADR-2606013600 P1) becomes an
*optional fast-seed cache* layered over the canonical block path, not the only
representation. The OPFS journal (P2) is unchanged.

# Consequences

- **One representation, one encoding.** Everything is true DAG-CBOR Datom blocks in
  Prolly Trees; the hot index is a derived projection. The "memory hot is a
  different implementation" discomfort is resolved, and the dedup/identity class of
  bugs disappears at the root.
- **Genuine IPLD interop.** Blocks become walkable by any DAG-CBOR/IPFS tool
  (tag-42 links, canonical bytes) — the codec label is now truthful.
- **Migration — block CIDs change.** True DAG-CBOR bytes differ from the old
  ciborium bytes, so every Prolly node (and therefore every commit/index root) gets
  a new CID. This is a **content re-address**, not a data loss: existing graphs are
  re-committed under the new encoding. Acceptable now (mostly seed/dev data); a
  hard format version tag guards readers. No on-the-wire dual-decode is provided —
  old blocks are re-ingested.
- **No substrate change, no new dependency tier.** Still kotoba Datom log + IPFS
  blocks (ADR-2605312345 / 2605262130). `serde_ipld_dagcbor` is a codec, not a new
  state backend. Murakumo-only inference, no-SQL, no-RW invariants untouched.
- **Performance neutral on the hot path** (D2 keeps the O(1) in-memory index);
  cold reads gain real IPLD interop at the same sha2-256 CID cost.

# Phases

- **P1 ✅ (this session)** — Gap B foundation: `kotoba-core::prolly` nodes encode as
  **true DAG-CBOR with tag-42 CID links** via `serde_ipld_dagcbor`, contained to the
  node codec (KotobaCid global serde unchanged). Tests assert tag-42 link presence,
  canonical round-trip, and CID stability; the workspace builds and the existing
  prolly/datomic suites stay green.
- **P2a ✅ (this session)** — Gap B + D1.1: `kotoba-kqe::keycodec` canonical
  order-preserving codec (sign-flip ints, total-order floats, NUL-escaped
  text/bytes, type segregation) with property tests for every trap; the
  Datomic-layer Prolly keys (`datom::*_key`, used by `kotoba-datomic::distributed`)
  route through it. Full suite green (core/datomic/kqe/graph/store).
- **P2b ✅ (this session) — first-tier Datomic is canonical; the bug is 2nd-tier.**
  Tracing the read/write paths settled the priority question (SPARQL is 2nd-tier;
  optimise first-tier Datomic first). Findings, all verified in code:
  - `kotoba-datomic` does **not** depend on `kqe::Arrangement::value_key` at all.
  - **First-tier writes/index** go through `kotoba-datomic::distributed`'s
    `datom::*_key` → now the canonical **keycodec** (P2a): numeric (sign-flipped)
    ints, total-order floats, NUL-safe text/bytes, type-tagged.
  - **First-tier `datomic.datoms` ordering** (`xrpc::datomic_datoms_sort_key`)
    sorts by **`EdnValue`'s derived `Ord`**, which compares `Integer(i64)`
    **numerically** (no `"100" < "20"`) and segregates types by variant order.
    Already correct; locked by tests (`kotoba-edn::ord_tests`,
    `xrpc::datomic_datoms_avet_orders_integers_numerically`).
  - Therefore **first-tier Datomic needs no further key-encoding work.** The
    `value_key` `String` bug (`n.to_string()` → `"100" < "20"`; non-{cid,text,int,
    enc} → `"?"`) is **confined to `kqe::Arrangement`**, the hot accelerator used
    only by the **2nd-tier `kotoba-graph::quad_store` (SPARQL/quad)** path.
- **P2b-SPARQL (deferred, 2nd-tier).** Migrating the QuadStore AVET (hot
  `value_key → Vec<u8>`, `pos` inner key `Vec<u8>`,
  `get_entities_by_attribute_value(attr, &Value)`, and threading a typed `Value`
  through the SPARQL planner instead of a stringified `object_key`) remains, gated
  by hot==cold parity tests. Deprioritised: SPARQL is 2nd-tier and the path is
  self-consistent today (equality-correct; only range/ORDER-BY on numeric AVET is
  lexicographic). Tracked, not done.
- **P2c (next)** — intrinsic dedup in `kqe::Arrangement` (no duplicate `push`),
  stable CID entity identity; remove the `kotoba-wasm` local patch in favour of the
  engine guarantee.
- **P3 ✅ (this session)** — Browser Prolly traversal over CID-verified blocks
  (ADR-2606013600 D5 follow-on). `kotoba-wasm` gains a **CID-verifying `BlockCache`**
  (`insert_verified` rejects any block whose bytes don't hash to its CID) +
  `hydrate_from_prolly(root, store)` which traverses the canonical tree with the
  **same `ProllyTree::scan_prefix` the server uses** (leaf values are
  `StoredDatom` = the same record shape the JSON path decodes) + `missing_cids`
  BFS driver so JS pulls a never-seen tree frontier-by-frontier (`block.get`),
  re-verifying each block, then hydrates. `web/kotoba-blocks.js` wires it to
  IndexedDB raw-block storage + remote `block.get`. The browser now reads the
  canonical content-addressed Datom log, not a bespoke snapshot. Native: 11
  kotoba-wasm tests (incl. multi-level block-sync + tamper rejection); JS↔wasm:
  CID-verify + `missingBlockCids` bindings; wasm32 builds.

# Honest risks

- `serde_ipld_dagcbor` canonical mode rejects some value shapes (NaN/Inf floats,
  non-string map keys in nested IPLD) — Datom values are scalars/bytes, so this is
  not expected to bite, but the encoder error path must surface, not panic.
- The block-CID re-address means any persisted store or hard-coded test CID must be
  regenerated; CI fixtures that pin CIDs need updating in the same change.
- D2 must be landed carefully so `hot_covers_all` short-circuits never return a hot
  result that the canonical projection wouldn't — covered by parity tests
  (hot result == cold Prolly result) on every query shape.

# Alternatives Considered

- **Make the hot path an in-memory Prolly Tree (full structural unification)** —
  rejected for now: turns O(1) point reads into O(log n) in-memory block walks and
  rewrites every loadtest-tuned path. D2's derived-projection gives the same "one
  structure" property without the perf regression. Kept as a possible future ADR.
- **Change `KotobaCid`'s global serde to tag-42 everywhere** — rejected: enormous
  blast radius (commit blocks, server JSON, StoredDatom, every persisted block).
  D1 contains tag-42 to the Prolly node codec; a system-wide CID-link pass is a
  separate decision.
- **Keep ciborium, only fix the comment/label** — rejected: leaves the codec label
  dishonest and the DAG non-interoperable, which is exactly the stated discomfort.

# References

- ADR-2605312345 — kotoba Datom log = first-class canonical state
- ADR-2605262130 — kotoba storage substrate unification
- ADR-2606013600 — kotoba browser node (P1/P2 landed; D5 Prolly traversal = P3 here)
- ADR-2605240001 — kotoba clean-room architecture (Prolly / EAVT / CID definitions)
- `40-engine/kotoba/crates/kotoba-core/src/{prolly.rs,cid.rs}` — node codec + CID
- `40-engine/kotoba/crates/kotoba-kqe/src/arrangement.rs` — hot index (Gap A)
- `40-engine/kotoba/crates/kotoba-datomic/src/distributed.rs` — covering Prolly roots
