---
id: adr-2606020200-session-close-kotoba-git
title: "ADR-2606020200: Session close — kotoba-git (git ↔ datomic + CID, round-trip)"
status: active
doc_type: adr
topic: session-close-kotoba-git
authoritative: false
last_verified: 2026-06-02
related:
  - adr-2606015000-kotoba-git-datomic-cid-roundtrip
supersedes: []
superseded_by: []
---

# ADR-2606020200: Session close — kotoba-git (git ↔ datomic + CID, round-trip)

**Status**: active
**Date**: 2026-06-02
**Deciders**: Jun Kawasaki

Documentation-only closure for the session answering
*「kotoba crate に git を datomic, cid ベースで対応できるようにしてください」*.
Authoritative design = **ADR-2606015000**.

# Context

There was no way to bring a git repository into kotoba. This session built a new
workspace crate `40-engine/kotoba/crates/kotoba-git` that represents git's object DAG
(blob / tree / commit / tag / ref) in kotoba in a datomic + CID-based way, with
**byte-exact round-trip fidelity**, in three increments.

# Decision

Shipped, per ADR-2606015000, to R0 with substrate invariants preserved (no external DB,
IPFS-compatible `KotobaCid`, no server keys; layered per ADR-2605312345 — blocks = backend,
Datom log = first-class state):

- **Increment 1 — codec + projection + round-trip.** `oid` (GitOid SHA-1), `object`
  (byte-exact framed codec), `schema` (`:git/*`), `datafy` (object → tx-data), `lib`
  (`GitStore` facade + query helpers), `repo` (loose-object disk import/export). Lossless
  anchor = framed bytes as a `KotobaCid` block; Datom projection records the SHA↔CID bridge
  (`:git/oid` ↔ `:git.object/cid`).
- **Increment 2 — packfiles (highest-value R0 gap).** `pack` module: pure-Rust pack v2 +
  idx v2 reader with `OBJ_OFS_DELTA`/`OBJ_REF_DELTA` recursive resolution; `repo::import_repo`
  ingests loose **and** packed (cloned / `git gc`'d) repos with no `git`/libgit2 binary.
- **Increment 3 — substantiate "datomic".** Tests query the projection through the real
  `kotoba_datomic::q` Datalog engine (all commits / `[(> ?size 3)]` predicate / input-bound
  commit→tree join) + annotated-tag full round-trip — all four object kinds covered.

# Consequences

- **Verified.** Codec proven against authoritative `git hash-object` / `git cat-file`
  vectors (empty blob `e69de29…`, `hello\n` `ce01362…`, tree `b4ed918…`, commit `ef01bd2…`).
  Two integration tests build real repos with the `git` CLI (one loose, one forced-packed
  via `git repack -ad` + `git gc --prune=now`) and assert every object materializes back to
  git's own oid; they skip gracefully if `git` is absent. **27 tests green** (24 unit + 1 doc
  + 2 integration), clippy clean.
- **Committed.** Crate in the kotoba submodule at `f480df3` (13 files, +2209 — only the
  kotoba-git files staged; unrelated concurrent passkey/auth/signal/wasm changes left
  untouched). Root docs (ADR-2606015000 + index + Status/crate-table rows) committed in root
  `807bb512c` (a concurrent background commit bundled them with its session-close work and
  regenerated the docs registry). `deps.toml` `[subdirs."crates/kotoba-git"]` registered.
- **Deferred (honest).** The root **submodule-pointer bump is not done** — `f480df3` sits
  atop 8 unrelated in-flight `kotoba-wasm` browser-node commits, so advancing root's pointer
  would pull those in; left to the coordinated pass that lands that work. Root still records
  kotoba `f14cef2` (docs-ahead-of-pointer interim state).
- **R0 limits.** Thin packs unsupported (REF_DELTA base must be in-pack); commit `parent`
  projection is a set (order preserved only in the lossless block); non-UTF-8 names/messages
  lossy in projection (lossless in block); sha256-format repos out of R0.

# Alternatives Considered

See ADR-2606015000 (structured-only reconstruction; reusing SHA-1 as the CID hash; shelling
out to `git cat-file`; `:db.type/ref` object relationships) — all deferred/rejected there.

# References

- ADR-2606015000 — authoritative design (kotoba-git: git object model as CID blocks + Datom projection)
- `40-engine/kotoba/crates/kotoba-git/` — crate (src incl. `pack.rs` + `tests/real_git_repo.rs`)
- ADR-2605262130 / ADR-2605312345 — kotoba substrate + Datom-first-class layering
- kotoba submodule commit `f480df3`; root docs commit `807bb512c`
