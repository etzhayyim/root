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
| `repo.clj` | `put-record` (block + EAVT projection), `record-cid`, `format-commit` (unsigned AT-Proto v3 commit object). |

### Verification (spec-exact, not a placeholder)

`bb test` checks every record CID against **go-ipfs 0.41 `ipfs dag put --store-codec
dag-cbor`** golden vectors — the pure-clj encoder is **byte-identical** to the
reference IPLD encoding (9 data vectors + the tag-42 CID-link vector). So record
and MST-node CIDs are spec-exact while living entirely on kotoba.

```bash
bb test   # 6 tests / 27 assertions green
```

## Next (separate increments)

1. **MST tree** — order record keys → record CIDs into the data root (atproto MST:
   leading-zero-of-sha256 fanout, node serialization as dag-cbor). Backed by this
   blockstore (MST nodes = `:block/*` datoms). Verify node CIDs vs `@atproto/repo`.
2. **Signed commit** — sign `format-commit` bytes with the member/operator key
   (no-server-key; the sig is the only non-kotoba secret, off-platform).
3. **CAR + `com.atproto.sync.*`** — `getRepo`/`getBlocks`/`getLatestCommit`/
   `subscribeRepos` over the blockstore → feeds `mst-projector` + federation.
4. **Wire into `etzhayyim-atproto-pds-clj`** — its `put-record` emits a repo block
   here; **P2 cutover** points `pds.etzhayyim.com` origin at the clj-on-kotoba PDS.

See ADR-2606242330 (PDS consolidation) §addendum for the kotoba-canonical-repo
invariant this module enforces.
