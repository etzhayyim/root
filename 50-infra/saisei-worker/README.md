# saisei-worker — public API + minimal interactive UI

Cloudflare Worker exposing `orgs/etzhayyim/com-etzhayyim-saisei/saisei/methods/{filing_plan,coverage_report}.cljc`
(required **verbatim**, unmodified logic — this Worker only adds HTTP routing, a
JSON wire adapter, and anonymous access logging) as a public HTTP API + a
one-page interactive UI. See `orgs/etzhayyim/com-etzhayyim-saisei/manifest.edn` for the actor's canonical
gates/non-goals — this Worker enforces none of them itself; it's a thin
transport over code that already enforces G2/G3/G4/G5/G7/G10.

**Live**: https://saisei-worker.04-feasts-minded.workers.dev (workers.dev
default subdomain — no custom domain yet; see "Custom domain" below).

## Why this is safe under `no-server-key` (ADR-2605231525 / 2606072802)

Read-only, stateless compute over public EDN data. No signing, no custody, no
state writes on a visitor's behalf — fits the read-only-public-compute
exemption cleanly (unlike e.g. yobel's Base L2 settlement, which needs a
member wallet/passkey signing flow).

## Routes

| Route | Method | Description |
|---|---|---|
| `/` | GET | Minimal interactive HTML page (vanilla JS, no build step, no client tracking script) |
| `/health` | GET | `ok` |
| `/api/coverage` | GET | JSON — jurisdiction coverage report (same shape as `bb ... coverage-report/coverage`) |
| `/api/filing-plan` | POST | JSON body `{"jurisdiction": "jp"}` → disclosed tracks for that jurisdiction (ALL registered procedures, never ranked — G2) |

`/api/filing-plan` accepts any of `jp`/`us`/`uk`/`de` (R0 seed); anything else
returns `"status": ":unknown-jurisdiction"` with an empty `tracks` array and a
generic referral (G10 — never guesses foreign law).

## Analytics — anonymous aggregate only

Access is logged via **Cloudflare Workers Analytics Engine** (binding
`SAISEI_ANALYTICS`, dataset `saisei_access`) — chosen specifically because it
writes server-side, aggregate time-series data points with **no cookies, no
per-visitor identity, no client-side tracking script** — the same posture
`tate`'s own test suite (`test_site.cljc`) enforces by asserting zero
gtag/analytics/pixel scripts in its static site.

Each data point: `blobs = [route, jurisdiction-or-empty, outcome]`,
`doubles = [1]` (a plain counter), `indexes = [YYYY-MM-DD UTC day bucket]`.
No IP, no user-agent, no cookie, no per-request timestamp beyond the day
bucket.

Query via the Analytics Engine SQL API (requires an API token with Analytics
Engine read access — separate from the deploy token):

```bash
curl "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/analytics_engine/sql" \
  -H "Authorization: Bearer <TOKEN>" \
  --data "SELECT blob1 AS route, blob2 AS jurisdiction, blob3 AS outcome, index1 AS day, sum(double1) AS count
          FROM saisei_access
          WHERE timestamp > NOW() - INTERVAL '7' DAY
          GROUP BY route, jurisdiction, outcome, day
          ORDER BY day DESC"
```

## Build / deploy

```bash
cd 50-infra/saisei-worker
npm install
npm run dev      # wrangler dev, local — runs the cljs build first (predev hook)
npm run deploy    # wrangler deploy — runs the cljs build first (predeploy hook)
```

The CLJS core (`cljs/src/saisei_worker/core.cljs`) requires
`saisei.methods.{edn,filing-plan,coverage-report}` **directly from
`orgs/etzhayyim/com-etzhayyim-saisei/saisei/methods/`** via a `:source-paths` entry in
`cljs/shadow-cljs.edn` — no duplicated logic. `ui.cljs` and `data_gen.cljs`
are generated (do not hand-edit):

```bash
bb 70-tools/scripts/saisei-worker/gen-ui.bb    # from 50-infra/saisei-worker/ui-src/page.html
nbb 70-tools/scripts/saisei-worker/gen-data.cljs  # from orgs/etzhayyim/com-etzhayyim-saisei/data/*.edn
```

Re-run both after editing `ui-src/page.html` or saisei's own `data/*.edn`,
before `npm run build`/`deploy`.

### A portability fix this Worker surfaced

`saisei.methods.edn`'s tokenizer originally used `re-matcher`/`.find`/`.group`
(Java-only `Matcher` API) — it compiled as `.cljc` but had never actually been
required from a `:cljs` build until this Worker, so the incompatibility was
latent. Fixed with a `#?(:clj ... :cljs ...)` split (JS `RegExp` `g`-flag
`.exec()` loop for `:cljs`); the babashka test suite (`run_tests.sh`, 14
tests/53 assertions) still passes unchanged since the `:clj` branch is
byte-identical to before.

## Custom domain (follow-up, needs zone:write)

The deploying Cloudflare token has `zone:read` only, not `zone:write`, so this
ships to the default `workers.dev` subdomain. To bind `saisei.etzhayyim.com`:
add a proxied DNS record for `saisei` under the `etzhayyim.com` zone, then add
a `[[routes]]` entry to `wrangler.toml` (`pattern = "saisei.etzhayyim.com/*"`,
`zone_name = "etzhayyim.com"`) and redeploy. This does **not** touch
`etzhayyim-did-web`'s existing `etzhayyim.com/*` catch-all route — a
subdomain-specific pattern on the same zone routes independently.

## Not yet done (deferred, see saisei's own ADR-2607061800 Consequences)

- No aozora.app profile registration yet (separate concern — the actor-split +
  `aozora:deploy` pipeline, deferred until this actor's own PR merges to
  `main`; toritsugi is the template for that step).
- No per-visitor rate limiting (low-stakes read-only compute; revisit if abuse appears).
- IVA (UK) intentionally has no self-file track — see saisei's own
  `coverage_report.cljc` structural-gaps note.
