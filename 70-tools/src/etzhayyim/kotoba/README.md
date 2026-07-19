# etzhayyim.kotoba — root-side Datom-log engine

Root-side realization of **ADR-2605262130 Phase 1/2** (kotoba storage substrate) and the
foundation for the encrypted-record envelope (#2, ADR-2605181100, next increment).

## Architectural boundary (the directive: 2026-06-14)

> *kotoba subrepo にはデータを置かず、データ・実装は root に置く.*

This is also what the ADRs already mandate. The boundary:

| Concern | Home | NOT in |
|---|---|---|
| Generic engine (Rust, CID/MST/Datalog/crypto) | `40-engine/kotoba/` **(git submodule, separate repo)** | — |
| Vocabularies / schemas | `00-contracts/schemas/*.kotoba.edn` | the kotoba subrepo |
| Datom data (the log + snapshots) | `80-data/**/*.kotoba.edn`, `80-data/datomic_mock/journal.edn` | the kotoba subrepo |
| Engine glue / interim runnable engine | **here** (`70-tools/src/etzhayyim/kotoba/`, on the bb classpath) | the kotoba subrepo |

Nothing here writes into `40-engine/kotoba/`. The subrepo stays the clean, generic,
Apache-2.0 engine (`brew install kotoba`); all religious-corp data + this glue live in root.

This **supersedes** the retired Python stub recorded by ADR-2607193500 (its `q()` always returned `[]`).

## Modules

| ns | role |
|---|---|
| `etzhayyim.kotoba.cid` | CIDv1 content-address (raw/sha2-256/base32) — **byte-identical to `ipfs add --cid-version=1 --raw-leaves`** and `orgs/etzhayyim/com-etzhayyim-rasen/methods/cid.py` (proven against the daemon-verified genome CIDs) |
| `etzhayyim.kotoba.datom` | `[e a v tx op]` model + EAVT/AEVT/AVET/VAET four-index arrangement |
| `etzhayyim.kotoba.query` | Datalog subset (`:find`/`:in`/`:where`, pattern joins, allowlisted predicates) |
| `etzhayyim.kotoba.schema` | load `00-contracts` schemas; value-type validation; cardinality-one auto-retraction |
| `etzhayyim.kotoba.log` | append-only EDN-lines journal + head CID + `.kotoba.edn` snapshot materializer |
| `etzhayyim.kotoba.engine` | public API: `connect` / `transact` / `q` / `entity` / `as-of` / `head-cid` / `snapshot!` |
| `etzhayyim.kotoba.crypto` | **XChaCha20-Poly1305 AEAD** (HChaCha20 + JDK ChaCha20-Poly1305) — validated bit-identical vs RFC 8439 §2.3.2/§2.8.2 + draft-irtf-cfrg-xchacha §2.2.1 |
| `etzhayyim.kotoba.encrypted` | `com.etzhayyim.encrypted.record` envelope (ADR-2605181100): `seal`/`open`, CID-over-ciphertext, AAD swap-resistance, `key-wrap` (Signal seam pluggable) |

## Usage

```clojure
(require '[etzhayyim.kotoba.engine :as kt])

(def conn (kt/connect {:journal "80-data/datomic_mock/journal.edn"
                       :schemas ["00-contracts/schemas/erp-ontology.kotoba.edn"]}))

(kt/transact conn [{:db/id "ch_1" :charge/amount 500 :charge/currency "USDC"}])

(kt/q conn '{:find  [?e ?amt]
             :where [[?e :charge/amount ?amt]
                     [(> ?amt 100)]]})
;; => #{["ch_1" 500]}

(kt/entity conn "ch_1")   ;; {:db/id "ch_1" :charge/amount 500 :charge/currency "USDC"}
(kt/as-of conn 1)         ;; live triples as of tx 1 (time-travel)
(kt/head-cid conn)        ;; "bafkrei…" content-address of the journal head
```

Reading an existing `80-data` log directly:

```clojure
(require '[clojure.edn :as edn]
         '[etzhayyim.kotoba.datom :as d]
         '[etzhayyim.kotoba.query :as q])
(def live (d/live-datoms (edn/read-string (slurp "80-data/genome/genome-datoms.kotoba.edn"))))
(q/q '{:find [?sym] :where [[?e :genome/kind :gene] [?e :gene/symbol ?sym]]} live)
```

## Test

```
bb test:kotoba
```

Covers CID framing + genome byte-identical parity, indexes, Datalog joins/predicates,
schema cardinality/validation, and engine durability + time-travel.

## CID digest note

The data-layer content address is **sha2-256 raw CIDv1** — the repo-canonical, ipfs-parity
digest used by `rasen/methods/cid.py` and the WASM loaders. kotoba-core's *internal block
frame* uses blake3-256; bind `etzhayyim.kotoba.cid/*hash*` to switch digests (the framing is
identical). Single raw block only (<256 KiB); larger artifacts chunk to UnixFS dag-pb.

## Increment #2 — encrypted-record envelope (LANDED)

ADR-2605181100 root-side reference impl: `crypto` (XChaCha20-Poly1305, KAT-validated) +
`encrypted` (the `com.etzhayyim.encrypted.record` envelope; CID computed over the ciphertext
envelope). Frozen, language-neutral **bit-identical test vectors** live at
`00-contracts/lexicons/com/etzhayyim/encrypted/test-vectors.json` (KATs + a frozen envelope),
machine-checked against the impl by `frozen-vectors-file-in-sync`. These are the
ADR-2605262130 Phase-5 acceptance basis: kotoba-crypto / kotoba-signal must reproduce the
exact bytes. All root-side; nothing written into the kotoba subrepo.

### Next
- keyWrap Signal layer (X3DH + Double Ratchet) — currently a pluggable `*wrap-key*` seam;
  the kotoba-signal reimplementation verifies against the same vectors.
- CBOR plaintext codec to match the production wire byte-for-byte (`*encode-plaintext*` seam).
- Wire `encrypted/seal` into `engine/transact` so confidential datoms ride the same log.
