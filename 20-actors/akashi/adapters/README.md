# akashi adapters

R1 adapter work starts with fixture-only parsers. No file in this directory may
perform live network collection unless a `sourcePolicySnapshot` has
`collectionStatus=allowed` and ADR-2606022300 R1 activation is attested.

Current parser:

- `regulator_bulk_fixture_parser.py` maps a local regulator-style bulk fixture
  into akashi lexicon-shaped records.
- `platform_ad_library_fixture_parser.py` maps reviewed local platform
  ad-library fixtures (Meta/Instagram and X samples) into the same akashi
  lexicon-shaped records. It has no network mode.
- `edn_export.py` projects validated records into deterministic
  Datomic/DataScript EDN tx-data. The caller chooses whether to store that EDN
  in git, DataLad/git-annex, or a future kotoba-git/kotoba-rad repository.
- `edn_query.cljc` loads the same tx-data and offers Datomic/DataScript-shaped
  query helpers for platform, advertiser, landing-domain, and count queries.
- `persist_fixture_edn.py` materializes the fixture tx-data and a storage
  manifest under `20-actors/akashi/data/`; outer git/DataLad/kotoba-rad tools
  perform the actual save/push.
- `lexicon_shape_validator.py` validates fixture parser output against the
  akashi lexicon subset used by these records.
- `dry_run_fixtures.py` parses and validates local fixtures, then prints counts
  or records. `--emit-edn` prints EDN tx-data. It has no network mode.
