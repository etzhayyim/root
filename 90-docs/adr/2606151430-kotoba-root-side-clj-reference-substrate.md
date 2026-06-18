---
id: adr-2606151430-kotoba-root-side-clj-reference-substrate
title: "ADR-2606151430: kotoba root-side Clojure reference substrate (data+impl in root, not the engine)"
status: proposed
doc_type: adr
topic: kotoba-root-side-clj-reference-substrate
authoritative: true
last_verified: 2026-06-15
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "Gives the religious-corp a runnable, validated, root-side realization of the kotoba Datom-log contract (ADR-2605262130 Phase 1/2) + the encrypted-record envelope (ADR-2605181100) without putting any religious-corp data or implementation into the generic kotoba engine repo."
authoritative_for:
  - kotoba-root-side-reference-engine
  - root-engine-data-boundary
  - encrypted-record-bit-identical-vectors
depends_on:
  - "2605262130"  # kotoba storage substrate unification (this is its root-side P1/2 realization)
  - "2605181100"  # com.etzhayyim.encrypted.* wire format (frozen; re-implemented here as the gate basis)
  - "2605312345"  # kotoba Datom = first-class canonical state ([e a v tx op])
  - "2606131645"  # kotoba submodule -> external repo (the "engine stays generic" boundary)
related:
  - "2606066001"  # keizu (power-network betweenness)
  - "2606022000"  # kabuto (supply-chain tier-depth / betweenness)
  - "2606012600"  # watatsuna (cable chokepoints / fragmentation)
  - "2606073600"  # hoshimori (orbit-ontology drift fix)
supersedes: []
superseded_by: []
---

# ADR-2606151430: kotoba root-side Clojure reference substrate

**Status**: proposed
**Date**: 2026-06-15
**Deciders**: Jun Kawasaki (founder = Council Lv7+ 1/1; PR review = Council attestation)

# Context

ADR-2605262130 names **kotoba** as the canonical storage substrate engine and lays out a
Phase 0→7 rollout; ADR-2606131645 then moved kotoba out of the tree (it is now the external
`etzhayyim/kotoba` repo, cloned on demand) so the in-tree engine is **generic, Apache-2.0, and
religious-corp-data-free**. That leaves two gaps for the religious-corp scope:

1. **No runnable root-side substrate.** The only in-root Datom implementation was
   `40-engine/datomic_emulator.py`, a stub whose `q()` always returned `[]`. Actors that want
   to load/query/validate their KG against the kotoba Datom-log contract had nothing to call.

2. **The data/impl boundary was a convention, not enforced.** The standing directive (restated
   2026-06-14) is: **religious-corp data + implementation live in root** (`00-contracts/` schemas,
   `80-data/` Datom data, `70-tools/src` glue) — **never inside the kotoba engine**. Nothing
   checked this.

The encrypted-record wire format (ADR-2605181100, `com.etzhayyim.encrypted.*`) is a frozen
constitutional artifact whose re-implementations must be **bit-identical**; there was no
root-side reference + vector suite to verify a re-implementation against.

# Decision

Add `etzhayyim.kotoba.*` — a runnable, validated, **root-side** Clojure/EDN realization of the
kotoba Datom-log contract — under `70-tools/src/etzhayyim/kotoba/` (on the `bb` classpath). It
**supersedes `40-engine/datomic_emulator.py`**. Everything lives in root; nothing is written to
the kotoba engine repo. Components:

- **engine / datom / log** — append-only EAVT log of `[e a v tx op]` (ADR-2605312345), the
  four-index arrangement (EAVT/AEVT/AVET/VAET), a **CIDv1 raw/sha2-256** content address that is
  byte-identical to `ipfs add --cid-version=1 --raw-leaves` and to `rasen/methods/cid.py`
  (proven against the daemon-verified genome CIDs), the ingest→log→snapshot lifecycle, and a
  schema-aware `transact` with a **write-path validation gate** (type / `:db/allowed` enum /
  `:db.unique` — atomic, opt-in via `:validate?`).
- **query** — a Datalog subset: pattern join, `[(pred …)]` predicates, `:in`, aggregates
  (`count`/`sum`/`min`/`max`/`avg` with group-by), `pull` (forward **and** reverse `:_attr`),
  and `not` / `or` / `and` clauses.
- **schema** — loads **five** ontology dialects found in `00-contracts/schemas/` (`:attributes`
  as a vector-of-`{:db/ident}` **or** a `{ident -> spec}` map; `:schema`; vocab-style
  `:node/edge/derived-attrs`); declared-attribute + value (type/enum) conformance.
- **crypto / cbor / encrypted** — XChaCha20-Poly1305 (HChaCha20 + JDK ChaCha20-Poly1305),
  validated bit-identical against **RFC 8439 §2.3.2/§2.8.2** + **draft-irtf-cfrg-xchacha-00
  §2.2.1**; canonical **CBOR (RFC 8949 §4.2)**; the `com.etzhayyim.encrypted.record` envelope
  (CID over the ciphertext) with a **frozen test-vector file** at
  `00-contracts/lexicons/com/etzhayyim/encrypted/test-vectors.json` — the ADR-2605262130
  Phase-5 bit-identical acceptance basis a Rust `kotoba-crypto` must reproduce.
- **metrics / graph** — HHI / effective-n / top-share + reachability / tier-depth / roots /
  **Brandes betweenness** / weakly-connected components — the concentration & chokepoint math
  the KG-mirror actors (kabuto / watatsuna / keizu) carry, now shared.
- **boundary / ingest / roster** — a lint that fails if a `*.kotoba.edn` data artifact appears
  inside an in-tree kotoba engine clone; a generic seed→log ingest CLI (`bb kotoba:ingest`); a
  roster maturity report (`bb kotoba:roster-report`).

**Invariant (enforced by `lint:kotoba-boundary` + by construction):** no religious-corp data or
implementation inside the kotoba engine. Schemas → `00-contracts/`; data → `80-data/` /
`20-actors/*/data/`; glue → `70-tools/src`.

# Consequences

- `bb test:kotoba` — **40 tests / 255 assertions green** (against the current roster). The whole
  discoverable roster (~21 actors, ~5,230 entities / ~39k live datoms) ingests with **zero
  undeclared-attr drift**; analysis is verified on real data (kabuto TSMC chokepoint betweenness
  449 / 5-tier chain; watatsuna Singapore+HK + fragmentation; keizu power broker).
- **Real schema-drift fixes** surfaced by the roster sweep and corrected in `00-contracts/`:
  `:watatsuna/note`, `:kabuto/note`, and 6 `:occ/* :op/*` orbit attrs (`hoshimori`) the seeds
  used but their ontologies had not declared.
- **One known value-baseline:** `mitooshi`'s `:forecast/{quantiles,probs,members}` hold inline
  structures while `forecasting-ontology` types them `:db.type/string`. Pinned as a
  characterization baseline (any *new* value drift fails) and flagged for actor-author
  reconciliation — the schema is **not** changed on a guess.
- **Out of scope:** the keyWrap Signal layer (X3DH + Double Ratchet) stays the `kotoba-signal`
  Rust crate's job; `*wrap-key*` is the seam. CLAUDE.md Status-row + `90-docs/_registry`
  indexing is a follow-up (per the ADR-2606131645 precedent of a separate registry PR).

# Alternatives Considered

- **Extend `datomic_emulator.py`.** Rejected: a Python stub with no Datalog; would re-grow a
  parallel non-conformant store.
- **Put the data/impl in the kotoba engine repo.** Rejected: violates the data-in-root boundary
  (ADR-2606131645) and pollutes the generic Apache-2.0 engine.
- **Wait for the Rust kotoba crates (Phase 1+) before any actor can use the substrate.**
  Rejected: blocks every 🟡 R0 actor; a root-side reference unblocks them now and gives the Rust
  engine a conformance/bit-identical target.

# References

- ADR-2605262130 — kotoba storage substrate unification (Phase 1/2 realized here)
- ADR-2605181100 — `com.etzhayyim.encrypted.*` wire format (vectors here are its gate basis)
- ADR-2605312345 — kotoba Datom = first-class canonical state
- ADR-2606131645 — kotoba submodule → external repo (the boundary this enforces)
- RFC 8439 (ChaCha20-Poly1305) · draft-irtf-cfrg-xchacha-00 (HChaCha20) · RFC 8949 (CBOR)
- `70-tools/src/etzhayyim/kotoba/README.md` — module map + usage
