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

Run CLJC adapter tests with `./20-actors/akashi/run_tests.sh`. Python adapter
files are intentionally absent.
