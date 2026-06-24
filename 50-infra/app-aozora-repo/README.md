# app-aozora-repo

> **Status: `R0` — AT Protocol repo layer in kotoba-clj, on the kotoba Datom log
> (ADR-2606242330 addendum).** The canonical record/MST block substrate for the
> aozora AppView's PDS, written so every block stays on the **kotoba Datom log**
> — never an `@atproto/repo` MemoryBlockstore / SQLite side store.

## Why this exists

The PDS consolidation (ADR-2606242330) makes `pds.etzhayyim.com` a single
`kotoba + clj + aozora` stack. Its repo layer (dag-cbor blocks → MST → signed
commit → `com.atproto.sync.*`) had two wrong options:

- **reimplement MST in clj from scratch** — huge, spec-fragile; or
- **reuse `@atproto/repo`** — but its default `MemoryBlockstore`/SQLite store
  would put repo state OUTSIDE kotoba, recreating the two-ledger problem the
  consolidation exists to kill.

`app-aozora-repo` is the third way: a **kotoba-clj** repo whose blocks are
content-addressed **Datoms on the canonical kotoba log** (ADR-2605312345). The
record's canonical form is its dag-cbor block; the `:record/*` datoms are a
queryable EAVT projection over the same log. The MST is the *interop wire* over
those blocks; IPFS is the block-backend tier.

```
record value ──lift $link──▶ dag-cbor block ──CIDv1(dag-cbor)──▶ kotoba Datom log
                                                                  [<cid> :block/bytes ..]   ← canonical
                                                                  [<uri> :record/cid ..]    ← EAVT view
MST root ──────────────────▶ unsigned v3 commit ──CID──▶ [<did> :repo/head <commit-cid>]
```

## What's implemented (R0, this module)

| ns | what |
|---|---|
| `dag_cbor.clj` | deterministic IPLD **dag-cbor** encoder (null/bool/int/text/bytes/array/map + tag-42 CID links; map keys length-first sorted; floats rejected). base32 decode to recover binary CIDs. |
| `cid.clj` | **CIDv1(dag-cbor)** framing (codec 0x71, sha2-256, base32 'b'). `block` / `cid-of`. |
| `blockstore.clj` | content-addressed **block store on the kotoba Datom log** (`BlockStore` protocol + `MemBlockstore`; blocks + repo head + record projection are all datoms). |
| `repo.clj` | `put-record` (block + EAVT projection), `record-cid`, **`commit-records!`** (full repo build — the PDS entry point). |
| `mst.clj` | atproto **Merkle Search Tree** (`data-root!`): keys → record CIDs, leading-zero fanout, layer-skip pass-through nodes, dag-cbor node serialization. |
| `commit.clj` | unsigned + **signed** AT-Proto v3 commit (`commit!`); `sign-fn` = member-key seam (no-server-key). |
| `car.clj` / `sync.clj` | CARv1 export + `com.atproto.sync.{getRepo,getLatestCommit,getBlocks}`. |

### Verification (spec-exact, cross-checked against the official impls)

`bb test` (**13 tests / 52 assertions**) checks:

- record/node **CIDs byte-identical to go-ipfs 0.41 `ipfs dag put --store-codec
  dag-cbor`** (9 data vectors + tag-42 CID-link);
- **MST root CIDs byte-identical to `@atproto/repo` `MST.getPointer()`** (empty /
  1 / 3 / 30-entry trees — incl. multi-layer + skip nodes);
- the **CARv1 export decodes under `@ipld/car`** with every block CID re-verified
  and the signed v3 commit decoding cleanly (cross-checked, see PR).

```bash
bb test   # 13 tests / 52 assertions green
```

## Status

1. ✅ **MST tree** — `mst/data-root!`, verified vs `@atproto/repo`.
2. ✅ **Signed commit** — `commit/commit!` with the no-server-key `sign-fn` seam.
3. ✅ **CAR + `com.atproto.sync.*`** — `getRepo`/`getLatestCommit`/`getBlocks`,
   verified vs `@ipld/car`. (`subscribeRepos` firehose = a later increment.)
4. ✅ **Wired into `etzhayyim-atproto-pds-clj`** — `etzhayyim.pds.repo` builds the
   repo from the PDS records via `commit-records!` and serves
   `com.atproto.sync.{getRepo,getLatestCommit,getBlocks}` (CARv1 / JSON) from
   `server.clj`; app-aozora-repo is on the PDS classpath. (`subscribeRepos`
   firehose + signed-on-write are later increments.) **P2 cutover** then points
   `pds.etzhayyim.com` origin at the clj-on-kotoba PDS → resolves the 530.

See ADR-2606242330 (PDS consolidation) §addendum for the kotoba-canonical-repo
invariant this module enforces.
