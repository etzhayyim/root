---
id: adr-2606015000-kotoba-git-datomic-cid-roundtrip
title: "ADR-2606015000: kotoba-git — git object model as CID blocks + Datom projection (round-trip)"
status: accepted
doc_type: adr
topic: kotoba-git
authoritative: true
last_verified: 2026-06-01
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - kotoba-git crate (git ↔ kotoba bridge)
  - SHA-1(git) ↔ KotobaCid(sha2-256) mapping for git objects
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
related:
  - adr-2605240001-kotoba-cleanroom-architecture
supersedes: []
superseded_by: []
---

# ADR-2606015000: kotoba-git — git object model as CID blocks + Datom projection (round-trip)

**Status**: accepted
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

**Landed**: crate committed in the kotoba submodule at `f480df3` (13 files, +2209;
27 tests green, clippy clean). Root docs (this ADR + index + Status/crate-table rows)
committed in root `807bb512c`. The root **submodule-pointer bump is intentionally
deferred** — `f480df3` sits atop 8 unrelated in-flight `kotoba-wasm` browser-node
commits, so advancing the pointer is left to the coordinated pass that lands that work
(root still records kotoba `f14cef2`; docs-ahead-of-pointer is the normal interim state).

# Context

Answers *「kotoba crate に git を datomic, cid ベースで対応できるようにしてください」*.

Git is already a content-addressed object DAG: every object is `<type> <size>\0<body>`
(the *framed* form) and its id (oid) is the SHA-1 of that framing. The four object kinds
are **blob** (file bytes), **tree** (sorted `<mode> <name>\0<20-byte-oid>` entries),
**commit** (header lines `tree`/`parent`*/`author`/`committer` + free-form headers like
`gpgsig` + blank line + message), and **tag** (annotated). Refs (`refs/heads/*`,
`refs/tags/*`, `HEAD`) point at oids (or, for `HEAD`, symbolically at another ref).

kotoba is itself a content-addressed Datalog database: every block is keyed by a
`KotobaCid` (CIDv1 dag-cbor sha2-256, IPFS-compatible — `kotoba-core::cid`) and the
canonical state is the Datom log over those blocks (ADR-2605312345). Before this ADR there
was **no** way to bring a git repository's history into kotoba: no crate, no schema, no
SHA↔CID mapping.

The two systems hash the same bytes in **different spaces** — git uses SHA-1, kotoba uses
sha2-256 — so the bridge must be explicit and bidirectional.

# Decision

Add a new workspace crate **`40-engine/kotoba/crates/kotoba-git`** that represents git in
kotoba in a datomic + CID-based way, with **byte-exact round-trip fidelity**. Two layers:

1. **Lossless anchor (CID block).** Every git object's exact framed bytes are stored as a
   `KotobaCid` block via `kotoba_store::put_verified` (which re-hashes and verifies
   `sha2-256(bytes) == cid`). Because the block is content-addressed, the git oid (SHA-1)
   is always recomputable from the bytes — this is what makes the round-trip byte-exact,
   independent of how richly we project the object into datoms.

2. **Datom projection (queryable EAVT).** Each object also becomes a small set of datoms,
   transacted through the existing `kotoba-datomic` facade, that (a) record the SHA↔CID
   bridge and (b) make the commit DAG / trees / refs Datalog-queryable. Schema (`:git/*`):

   | attribute | type | notes |
   |---|---|---|
   | `:git/oid` | string | 40-hex SHA-1; **`:db.unique/identity`** → idempotent upsert + SHA side of bridge |
   | `:git.object/kind` | keyword | `:blob` / `:tree` / `:commit` / `:tag` |
   | `:git.object/cid` | `#cid` | KotobaCid of framed bytes — **CID side of bridge** |
   | `:git.object/size` | long | body length |
   | `:git.commit/{tree,author,committer,message}` | string | scalar header fields |
   | `:git.commit/parent` | string | **cardinality/many** oid hexes |
   | `:git.tree/entry` | string | **cardinality/many**, `"<mode> <oid> <name>"` |
   | `:git.tag/{object,type,name,tagger,message}` | string | annotated-tag fields |
   | `:git.ref/{name,target,symbolic}` | string | `name` is **`:db.unique/identity`** |

This layering is a direct instance of ADR-2605312345: the content-addressed blocks are the
**block backend**, the Datom log is the **first-class queryable state** over them.

**Module map**: `oid` (GitOid SHA-1) · `object` (byte-exact framed codec — the fidelity
core) · `schema` (`:git/*` install tx) · `datafy` (object → tx-data) · `pack` (pure-Rust
pack v2 + idx v2 reader with OFS/REF delta resolution) · `lib` (`GitStore` facade:
`put_object`/`put_ref`/`materialize_framed`/`materialize_object` + query helpers
`object_cid`/`all_objects`/`commit_parents`/`log`/`list_refs`/`resolve_ref`) · `repo` (disk
loose-object + refs reader/writer, `import_loose_repo` (loose-only) / `import_repo`
(loose + packed) / `export_repo`).

**Round-trip definition.** Fidelity is defined over the *framed object bytes* (hence the
oid), **not** over the on-disk zlib stream. `materialize_framed` reads the CID block back,
recomputes SHA-1, and errors (`OidMismatch`) unless it equals the requested oid.

# Consequences

- **Verified against real git.** The codec is proven against authoritative
  `git hash-object` / `git cat-file` vectors (empty blob `e69de29…`, `hello\n` blob
  `ce01362…`, single-entry tree `b4ed918…`, commit `ef01bd2…`). Two integration tests
  (`tests/real_git_repo.rs`) build actual repos with the `git` CLI — one **loose**, one
  forced **packed** via `git repack -ad` + `git gc --prune=now` — import them, and assert
  every object materializes back to git's own oid; they skip gracefully if `git` is absent.
  **27 tests green** (24 unit + 1 doc + 2 integration), clippy clean.
- **The "datomic" promise is substantiated through the real engine.** Tests query the git
  projection with `kotoba_datomic::q` Datalog (not just the typed scan helpers): "all
  commits" (`[?e :git.object/kind :commit]`), "blobs over N bytes" (`[(> ?size 3)]`
  predicate), and an input-bound join from a commit oid to its tree — plus an annotated-tag
  full round-trip whose `:git.tag/*` fields are queryable. So the commit DAG is genuinely
  Datalog-addressable, not merely scannable.
- **Packfiles decoded (pure-Rust).** `import_repo` reads `objects/pack/*.{idx,pack}` (idx
  v2 fanout/oid/offset tables incl. the 8-byte large-offset table; pack v2 object headers;
  `OBJ_OFS_DELTA` + `OBJ_REF_DELTA` resolved recursively via copy/insert delta application)
  — so cloned / `git gc`'d repos round-trip too, no `git` binary or libgit2 needed.
- **Idempotent import.** `:git/oid` unique-identity means re-importing the same object
  upserts to one entity — safe to re-run `import_loose_repo`.
- **Substrate-faithful.** Blocks are IPFS-compatible `KotobaCid`s; no external DB, no
  Kotoba/Datomic, no new substrate-engine name — only `kotoba-core`/`-store`/`-datomic`/`-edn`
  (substrate invariants ADR-2605262130 preserved). No server-held keys; pure read/transform.
- **Honest R0 limits.** (1) **Thin packs not supported** — on-disk packs are self-contained
  so every REF_DELTA base resolves within the loaded pack set; a thin pack (delta base
  outside the pack, e.g. mid-fetch wire packs) would fail to resolve. Loose `import_loose_repo`
  still reports `packs_present` for callers who want loose-only. (2) The commit
  `parent` projection is a *set* (Datomic cardinality-many), so per-parent **order** is not
  preserved *in the datoms* — but the lossless framed block preserves it, so round-trip is
  unaffected; order-sensitive queries should read the block. (3) Non-UTF-8 tree names /
  commit messages are stored lossily *in the projection* (lossless in the block). (4) SHA-256
  git repos (`extensions.objectFormat=sha256`) are out of R0.

# Alternatives Considered

- **Reconstruct objects purely from structured datoms (no raw block).** Rejected: commits
  carry free-form, order-sensitive headers (`gpgsig`, `encoding`, `mergetag`); a structured-
  only model risks byte drift and a broken oid. Storing the framed block makes fidelity
  unconditional and the datoms a pure convenience projection.
- **Map git oid directly into a KotobaCid (reuse SHA-1 as the CID hash).** Rejected: kotoba
  CIDs are sha2-256; minting non-canonical SHA-1 CIDs would break `is_ipfs_compatible` and
  the block store's `put_verified` check. The explicit `:git/oid` ↔ `:git.object/cid` bridge
  keeps both hash spaces canonical.
- **Shell out to `git cat-file --batch` for reads.** Rejected as the core path (adds a git
  binary runtime dependency, against kotoba's self-contained substrate ethos). Used only in
  the optional integration test for cross-checking against real git.
- **`:db.type/ref` relationships between objects.** Deferred: would require topological
  import ordering and lookup-ref upserts; oid-string edges are simpler, order-independent,
  and still joinable. Ref-type upgrade is future work.

# References

- `40-engine/kotoba/crates/kotoba-git/` — crate (src incl. `pack.rs` + `tests/real_git_repo.rs`)
- ADR-2605262130 — kotoba storage substrate unification (no parallel engine, IPFS block backend)
- ADR-2605312345 — kotoba Datom log = first-class canonical state; blocks = backend
- ADR-2605240001 — kotoba clean-room architecture (CID + EAVT)
- Git internals — object format (`<type> <size>\0<body>`, SHA-1 oid), tree/commit/tag layout
