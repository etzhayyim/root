# Python → clj/cljc port status (ADR-2606280030)

Status: **partial**. Pure-logic cores ported to idiomatic `.cljc` under `clj/`
(`bb run_tests.clj` -> 22 tests / 88 assertions green). ALL `.py` are KEPT -- the
pipeline is deployed (rust/cc-phase3, wasm appview, live RisingWave tables) and the
ported namespaces are not yet wired in. `py_removed = 0`.

## Ported (verified under bb)

| cljc ns | mirrors .py | notes |
|---|---|---|
| `common-crawl.did` | `scripts/phase3h_transform_parquet.py` | SSoT `page-did-from-url` / `encode-segment` / `domain-to-slug` / `url-path` -- byte-exact vs Python + Rust (`rust/cc-phase3/src/main.rs`). parquet I/O stays in .py (pyarrow hard dep). |
| `common-crawl.intel` | `scripts/phase4_intel_risingwave.py` | `parse-json` / `clamp-intel` / `intel-prompt` / `enriched-description` + Murakumo loopback call. RunPod fallback + its hard-coded key NOT ported (Murakumo-only, ADR-2605215000). RW read/UPDATE -> store seam. |
| `common-crawl.inject` | `scripts/phase5_inject_did.py` | jsonl/cypher domain loaders, slug/DID derivation, PDS `identity.create` + `createRecord` payloads, XRPC via `babashka.http-client`. `load_domains_from_risingwave` -> store seam. |
| `common-crawl.cypher` | `scripts/phase5b_inject_pages.py` | Cypher-batch parsing (full/short page, HOSTS_PAGE, LINKS_TO) + per-label write records + `process-batch-lines` filter/dedup. |
| `common-crawl.store` | (cross-cutting) | injectable `Store` protocol = the kotoba-Datom-log / graph-adapter / in-mem seam that REPLACES the forbidden direct RisingWave/psycopg coupling. |

## Remaining (kept as .py -- heavy deps / bulk SQL; mark partial)

- `scripts/phase3h_transform_parquet.py` -- pyarrow parquet read/write loop (only the
  per-row DID logic was ported; the I/O is a pyarrow hard dep -- do NOT reimplement).
- `scripts/phase3g_copy_ingest.py`, `scripts/phase3i_alias_backfill.py` -- psycopg2 bulk
  INSERT / 985M-row JOIN against RisingWave (substrate boundary forbids RisingWave as
  canonical state; real port = re-target the `Store` seam at the kotoba Datom log).
- `scripts/phase3j_s3_upload_v2.py`, `scripts/s3_upload_parallel.py` -- boto3 S3 upload.
- `scripts/phase4_intel_risingwave.py`, `scripts/phase5_inject_did.py`,
  `scripts/phase5b_inject_pages.py` -- drivers (main, ProcessPool/Thread orchestration,
  resume-state files, signal handling) kept in .py; their pure cores are ported above.
- `scripts/phase_coverage_gap.py` -- psycopg2 coverage analysis (RisingWave).
- `scripts/archive/*.py` -- already-archived legacy SQL/ingest paths; not ported.

Coexistence rule: a `.py` is removed only once its cljc twin is verified AND
grep-confirms nothing imports it AND it is not wired to a live deploy. None qualify yet.
