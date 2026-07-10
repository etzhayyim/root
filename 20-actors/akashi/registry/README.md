# akashi registry

Registry files are policy inputs for `akashi`; they do not authorize live
collection by themselves.

- `source-catalog.seed.json` lists candidate public disclosure source families.
- `source-policy-reviews.seed.json` records the R0/R1 review workflow state for
  each source. Meta/X official API paths are allowed and token-gated; all other
  live collection remains disabled.
- `source-policy-approval.schema.json` defines the transaction shape for future
  source runtime changes.
- `source-policy-approval.fixture-only.example.json` is a non-live example that
  promotes only the local regulator fixture parser.
- `source-policy-approval.meta-official-api.json` and
  `source-policy-approval.x-dsa-repository-api.json` authorize only official API
  access. They do not authorize scraping, logged-in UI automation, or anti-bot
  bypass.

The review registry is deliberately data-driven so an adapter can be disabled
without code changes.
