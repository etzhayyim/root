---
id: doc-260424-oauth-strict-mode-cutover
title: "OAuth cnf.jkt strict-mode cutover runbook (ADR-2604240914 Y1 A3)"
status: active
doc_type: how-to
topic: auth-lifecycle
authoritative: true
last_verified: 2026-04-24
authoritative_for:
  - DPOP_CNF_JKT_ENFORCEMENT=warn → strict cutover procedure
  - pre-flip validation checklist
  - rollback procedure on incident
related:
  - adr-2604240914-oauth-rs-binding-revocation-introspection
  - adr-2604231821-atproto-oauth-wire-format-snake-case
---

# Context

ADR-2604240914 Y1 A2 plumbs DPoP `cnf.jkt` through OAuth session issuance
and the RS verify path. ADR-2604240914 Y1 A3 staged the enforcement as a
one-line env flip:

```
DPOP_CNF_JKT_ENFORCEMENT=warn     # default — log mismatches, pass through
DPOP_CNF_JKT_ENFORCEMENT=strict   # reject mismatches with 401 invalid_dpop_proof
```

`warn` mode ships in the initial deploy so legacy tokens issued before Y1 A2
(no `cnf.jkt` claim) don't break. After a ~2-week observation window the flip
to `strict` closes the grace door.

This runbook is the procedure for that flip.

# Pre-flip validation (T-0, before flipping)

## 1. Warn-log volume must be ≈ 0

`dpopResourceServerMiddleware` emits two grace-path warn lines
(`src/middleware/dpop.ts:120,136`):

- `[dpop/rs] access token missing cnf.jkt (grace)` — legacy token
  without the binding claim. Expected to approach zero as pre-Y1-A2
  refresh tokens roll over.
- `[dpop/rs] cnf.jkt ↔ proof jkt mismatch (grace)` — **must** be zero.
  Non-zero = client bug or impersonation attempt.

### Query — Logpush + jq

Cloudflare Logpush writes atproto Worker stderr to B2 as gzipped NDJSON,
one object per log line. The strict-mode gate is **≤ 1 `missing` event
/ hour averaged over 14 days + 0 `mismatch` events across the full
window.** Representative probe (adjust `$BUCKET` / `$PREFIX` to match
the live job):

```bash
# Last 24h of [dpop/rs] warn lines grouped by message pattern.
# Run from dev laptop or CI; needs read-only R2 credentials.
export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=...
export R2_ENDPOINT=https://<account>.r2.cloudflarestorage.com
BUCKET=logpush-atproto
SINCE=$(date -u -v-24H '+%Y-%m-%dT%H')

aws s3 --endpoint-url "$R2_ENDPOINT" ls "s3://$BUCKET/" \
  | awk -v since="$SINCE" '$0 ~ since || $0 > since {print $4}' \
  | while read -r key; do
      aws s3 --endpoint-url "$R2_ENDPOINT" cp "s3://$BUCKET/$key" - \
        | gunzip -c
    done \
  | jq -r '
      (.Logs // []) as $logs
      | ($logs[]?.Message? // $logs[]?.message? // "")
      | strings
      | capture("\\[dpop/rs\\] (?<kind>access token missing cnf\\.jkt|cnf\\.jkt ↔ proof jkt mismatch)").kind
    ' \
  | sort | uniq -c
```

**Pass criteria (both must hold for 14 consecutive days):**

| Pattern | Threshold |
|---|---|
| `access token missing cnf.jkt` | ≤ 24 events / 24h window (= 1/hr avg) |
| `cnf.jkt ↔ proof jkt mismatch` | **0 events** / 24h window |

Any `mismatch` hit → investigate by IP / UA before the flip. Any
`missing` spike → find the stale client (usually a bot using an old
refresh token).

### Fallback — `wrangler tail` for an ad-hoc 1-minute probe

When Logpush is unavailable (e.g. during rehearsal before the job is
wired) the automated preflight (§Automated preflight below) samples
`wrangler tail` directly. Manual equivalent:

```bash
wrangler tail --format=json etzhayyim-pds-2603241700 \
  | jq -r '
      (.logs // []) as $logs
      | ($logs[]?.message? // [])
      | if type == "array" then .[] else . end
      | strings
      | select(test("\\[dpop/rs\\].*(missing cnf.jkt|mismatch)"))
    ' \
  | tee /tmp/dpop-grace-hits.log
```

## 2. All CLI / agent clients emit cnf.jkt

The issuance side (`/oauth/token`) already does this for every DPoP-bound
flow as of commit `0cbfcfd3845` (2026-04-23). Re-confirm by:

```bash
# Mint a fresh token via etzhayyim CLI (issues with cnf.jkt post-A2 deploy).
etzhayyim authn signin
# Grab the access token from ~/.etzhayyim/auth.json and decode:
jq -r .api_key ~/.etzhayyim/auth.json | cut -d. -f2 | base64 -d | jq .cnf
# Expect: {"jkt": "<thumbprint>"}
```

For `sk_live_*` API keys: these are **not** DPoP-bound and won't carry
`cnf.jkt`. They travel on `Authorization: Bearer` not `DPoP`, so
`dpopResourceServerMiddleware` never evaluates them. Unaffected by the flip.

### Automated preflight

All three gates above (§1 warn-log volume, §2 cnf.jkt issuance, §3 staging
smoke — landed below) are encoded in
`50-infra/cloudflare/workers/atproto/scripts/oauth-strict-mode-preflight.sh`.
Run it before any flip; exit 0 is a hard gate on the runbook:

```bash
cd 50-infra/cloudflare/workers/atproto
# Against staging (SAMPLE wrangler tail + smoke against staging.atproto.etzhayyim.com)
STAGING=1 bash scripts/oauth-strict-mode-preflight.sh

# Against production (after 24h staging soak)
bash scripts/oauth-strict-mode-preflight.sh
```

Exit codes: 0 = all 3 gates green, safe to flip; 1 = first failing gate
printed, do NOT flip. Knobs: `MIN_DEPLOY_AGE_DAYS`, `TAIL_SECS`,
`MAX_MISSING_PER_MIN`, `MAX_MISMATCH_PER_MIN`, `SKIP_TAIL`, `SKIP_SMOKE`.

## 3. Smoke test passes against staging in strict mode

Temporarily flip staging first:

```bash
cd 50-infra/cloudflare/workers/atproto
# Edit wrangler.jsonc: "DPOP_CNF_JKT_ENFORCEMENT": "strict"
wrangler deploy --env staging
ORIGIN=https://staging.atproto.etzhayyim.com bash scripts/oauth-smoke.sh
```

The smoke script exercises the spec-compliant happy path (Bearer / DPoP
with matching cnf.jkt) plus the 401 rejection paths. Run for ≥ 24h in
staging before touching production.

# Flip procedure (T-0 production)

```bash
cd 50-infra/cloudflare/workers/atproto

# 1. Edit wrangler.jsonc
# Change:
#   "DPOP_CNF_JKT_ENFORCEMENT": "warn"
# To:
#   "DPOP_CNF_JKT_ENFORCEMENT": "strict"

# 2. Deploy
wrangler deploy

# 3. Smoke
bash scripts/oauth-smoke.sh

# 4. Grep for the strict-rejection log signature
# (shouldn't appear — if it does, rollback).
#   [dpop/rs] proof verification failed
#   invalid_dpop_proof
```

# Rollback

Single env var change. Rollback = flip back to `warn` + redeploy. No data
state changes, no session invalidation.

```bash
# In wrangler.jsonc: restore "DPOP_CNF_JKT_ENFORCEMENT": "warn"
wrangler deploy

# Expected recovery: any client that was failing with
# invalid_dpop_proof should now flow through again (warn-only).
```

Cache side-effect: the per-Worker `_dpopJtiCache` and `_dpopNonceCache` are
in-memory — rollback redeploy clears them. First post-rollback request from
a given client gets a fresh nonce via the standard `use_dpop_nonce`
response.

# Observability hooks

| Signal | Source | Threshold |
|---|---|---|
| Warn `[dpop/rs] access token missing cnf.jkt (grace)` rate | atproto Worker Logpush, §1 jq query | ≤ 1/hr averaged over 14d → safe to flip |
| Warn `[dpop/rs] cnf.jkt ↔ proof jkt mismatch (grace)` rate | same | **= 0** over 14d; any hit = investigate before flip |
| 401 `invalid_dpop_proof` rate | OCEL Analytics Engine (`auth_level`+`status=401`) | <1% of DPoP traffic post-flip; spike = rollback |
| `/oauth/revoke` 200 rate | Logpush | sanity — ensure revocation still flows |
| nonce rotation errors | Worker logs | `[dpop/rs] proof verification failed` should not surge |

# Post-flip cleanup (T+14d after flip)

Once strict mode has run for 2 weeks without incident:

1. Remove the `DPOP_CNF_JKT_ENFORCEMENT` env var entirely from `wrangler.jsonc`.
2. Delete the grace-path branches in `middleware/dpop.ts`:
   - Remove the `enforcement / strict` variable reads.
   - Make the missing / mismatch return `json401(...)` unconditionally.
3. Drop the `[Y1 A2 grace]` test cases in `middleware/dpop.test.ts` — only
   `[Y1 A3 strict]` cases remain.
4. Update ADR-2604240914 status: `Y1 A3` → "cutover complete".

# References

- ADR: `90-docs/adr/2604240914-oauth-rs-binding-revocation-introspection.md`
- Smoke: `50-infra/cloudflare/workers/atproto/scripts/oauth-smoke.sh`
- Middleware: `50-infra/cloudflare/workers/atproto/src/middleware/dpop.ts`
- Tests: `50-infra/cloudflare/workers/atproto/src/middleware/dpop.test.ts`
