# akashi adapters

R1 adapter work starts with fixture-only parsers. No file in this directory may
perform live network collection unless a `sourcePolicySnapshot` has
`collectionStatus=allowed` and ADR-2606022300 R1 activation is attested.

Current adapter surface:

- `regulator_bulk_fixture_parser.cljc` maps a local regulator-style bulk fixture
  into akashi lexicon-shaped records.
- `platform_ad_library_fixture_parser.cljc` maps reviewed local platform
  ad-library fixtures (Meta/Instagram and X samples) into the same akashi
  lexicon-shaped records. It has no network mode.
- `ingest_platform_ad_library.cljc` is the operator-facing reviewed-export
  ingest CLI for local Meta/Instagram/X-style JSON snapshots. It has no
  network mode; it can emit records, DataScript/kotoba tx EDN, or a Datomic
  schema+scalar tx bundle.
- `official_api_ingest.cljc` is the production official-API boundary. It is
  limited to Meta Ad Library API and X DSA Ads Repository API/CSV exports. It
  requires operator-provided tokens and has no scraping or UI automation mode.
- `edn_export.cljc` projects validated records into deterministic
  DataScript/kotoba EDN tx-data and a Datomic import bundle with schema plus
  scalar `:db/add` ops. The caller chooses whether to store that EDN in git,
  DataLad/git-annex, or a future kotoba-git/kotoba-rad repository.
- `edn_query.cljc` loads the same tx-data and offers Datomic/DataScript-shaped
  query helpers for platform, advertiser, landing-domain, and count queries;
  it can also materialize the Datomic scalar tx bundle for the same reads.
- `persist_fixture_edn.cljc` materializes the fixture tx-data and a storage
  manifest under `20-actors/akashi/data/`; outer git/DataLad/kotoba-rad tools
  perform the actual save/push.
- `lexicon_shape_validator.cljc` validates fixture parser output against the
  akashi lexicon subset used by these records.
- `dry_run_fixtures.cljc` parses and validates local fixtures, then prints counts
  or records. `--emit-edn` prints EDN tx-data. It has no network mode.

Run CLJC adapter tests with `nbb 20-actors/akashi/run_tests.cljs`. Python adapter
files are intentionally absent.

Production examples:

```bash
META_AD_LIBRARY_ACCESS_TOKEN=... bb -m akashi.adapters.official-api-ingest meta \
  --search-terms "public interest" --countries EU --limit 25 --materialize

X_ADS_REPOSITORY_BEARER_TOKEN=... bb -m akashi.adapters.official-api-ingest x-create-export \
  --user-id 123456 --geo-location DE --start-date 2026-07-01 --end-date 2026-07-10

bb -m akashi.adapters.official-api-ingest x-csv \
  --csv /path/to/x-dsa-export.csv --materialize
```
