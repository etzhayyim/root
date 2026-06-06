# Gov Fetch Coverage Runbook

This runbook separates government website pipeline coverage from public-site
reachability. A missing `last_content_hash` is not automatically a pipeline
failure: DNS, TLS, HTTP, and timeout failures are tracked separately on
`vertex_gov_org`.

## Read Model

Canonical view:

```sql
SELECT * FROM view_gov_fetch_coverage ORDER BY unreachable DESC, domain_code;
```

Key fields:

- `with_website`: org rows with a non-empty official website.
- `fetch_checked`: website rows that have a recorded fetch diagnostic.
- `reachable`: checked rows that produced a hash, or had `direct_ok`, `proxy_ok`, or `wet_chunk`.
- `hashable`: rows considered hashable from current evidence; includes historical hashes without a fresh diagnostic.
- `hashed`: website rows with `last_content_hash`.
- `unreachable`: checked rows that still have no hash and a non-success fetch status.

Derived metrics:

- `hashCoveragePct = hashed / with_website`
- `reachabilityCoveragePct = reachable / fetch_checked`
- `hashableSiteCoveragePct = hashed / hashable`

## CLI

Run from `30-graph/graph-schema`:

```bash
DATABASE_URL="$KOTOBA_URL" pnpm verify:gov-fetch
```

Limit to selected country/domain codes:

```bash
GOV_FETCH_COVERAGE_DOMAINS=afg,rus,chl DATABASE_URL="$KOTOBA_URL" pnpm verify:gov-fetch
```

If running locally, port-forward Kotoba/Datomic first and rewrite the host to
`127.0.0.1:4566`.

## Operational Interpretation

- `unchecked` means the row has not yet been diagnosed by the Python actor.
- `proxy_http_530` normally indicates upstream DNS/Cloudflare reachability failure.
- `proxy_http_526` indicates TLS verification failure at the proxy edge.
- `proxy_http_502` or `timeout` should be retried at low rate before declaring the site unreachable.
- `hashableSiteCoveragePct` is the best pipeline-health metric.
- `hashCoveragePct` includes public websites that are offline or misconfigured, so it should not be used alone as pipeline health.

## Backfill Pattern

Use the Zeebe/Python actor image in a one-off pod instead of running large
batches inside the live worker. Keep country batches small, e.g. `limit=3` to
`limit=10`, and set `postUpdates=false`.

Expected result for unreachable sites is not a hash increase; it is a populated
`last_fetch_status`, `last_fetch_error`, and `last_fetch_checked_at`.
