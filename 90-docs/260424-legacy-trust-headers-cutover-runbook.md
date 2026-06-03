---
id: doc-260424-legacy-trust-headers-cutover
title: "Legacy trust-header cutover runbook — LEGACY_TRUST_HEADERS on → off (ADR-2604241038 Phase γ2)"
status: active
doc_type: how-to
topic: auth-lifecycle
authoritative: true
last_verified: 2026-04-24
authoritative_for:
  - LEGACY_TRUST_HEADERS=on → off cutover procedure
  - PDS + AppView + chat + signal trust-plane unification finish line
  - per-Worker smoke validation post-cutover
  - rollback procedure when HMAC-only traffic starts failing
related:
  - adr-2604241038-yoro-pds-ideal-topology
  - doc-260424-oauth-strict-mode-cutover
  - doc-260424-oauth-appview-staging-deploy-checklist
---

# Context

ADR-2604241038 Contract 3 unifies the Worker-to-Worker viewer-DID trust
plane on an HMAC-signed 3-header envelope:

```
x-etzhayyim-viewer-did:        did:web:alice.etzhayyim.com
x-etzhayyim-viewer-issued-at:  <unix seconds>
x-etzhayyim-viewer-signature:  HMAC-SHA256(APPVIEW_INTERNAL_SECRET, "did|issued-at")
```

The PDS (upstream) emits the trio on every pipethrough; the AppView /
chat / signal Workers (downstream) verify it. The HMAC rollout ships
with the legacy path still enabled so downstream Workers that haven't
redeployed yet don't fail closed.

`LEGACY_TRUST_HEADERS` controls the grace behaviour on both sides:

| Worker  | when `on` (default) | when `off` |
|---|---|---|
| atproto (PDS) | emits legacy `x-etzhayyim-authenticated-did` + `x-etzhayyim-internal-trust` **alongside** the HMAC trio | emits **only** the HMAC trio |
| bsky (AppView) | accepts legacy shared-secret header pair if HMAC verify fails | rejects legacy pair, drops viewer to anonymous |
| chat | (same as bsky — currently only logs the viewer DID; flag wired for future per-viewer state) | (same) |
| signal | (same — scaffold 501s today, flag is pre-wired for the real handlers) | (same) |

This runbook is the procedure for flipping the flag to `"off"` — the
grace-window close that deletes the attack surface of the plain-text
shared secret.

# Pre-flip validation (T-0, before flipping)

## 1. Confirm HMAC trio rollout is ≥14 days old

`APPVIEW_INTERNAL_SECRET` must have been in Secrets Store **and** the
PDS + all downstream Workers deployed with the HMAC code for at least
two weeks. Verify via:

```bash
# Dates of the atproto redeploy carrying `applyViewerHeaders`:
wrangler deployments list --name etzhayyim-pds-2603241700 | head -5
# Same for appview, chat, signal:
wrangler deployments list --name etzhayyim-appview | head -5
wrangler deployments list --name etzhayyim-chat | head -5
wrangler deployments list --name etzhayyim-signal | head -5
```

If any Worker's latest deploy is < 14 days old, **do not flip**. The
point of the grace window is the case where one Worker got stuck on an
old build and still needs legacy headers.

## 2. Warn-log volume must be ≈ 0

The probe log is **already shipped** (commit `e9abc5db49b`, 2026-04-24):

```ts
// appview/src/handlers/appview.ts trustedViewerDid() legacy branch:
console.warn(
  `[trust][legacy] hit did=${claimed.slice(0, 32)} matched=${matched}`,
);
```

Same pattern lands in chat + signal once their real handlers migrate
(Phase δ2 / δ3); scaffolds return 501 today so there's no legacy-path
surface on those Workers yet. For now the measurable signal is
appview-only, which is fine — it's the only Worker that actually
exercises viewer-DID resolution against real traffic.

### Query — Logpush + jq

Cloudflare Logpush writes Worker stderr to the configured B2 bucket
(`logpush-appview/…/*.log.gz`) as NDJSON with one object per log line.
The γ2 observation gate is **0 `[trust][legacy] hit` events per rolling
24-hour window for 14 days** before flipping. Representative probe
(adjust `$BUCKET` / `$PREFIX` to match the live Logpush job):

```bash
# Counts matched vs unmatched legacy hits per UTC hour over last 24h.
# Run from dev laptop or CI; needs read-only R2 credentials.
export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=...
export R2_ENDPOINT=https://<account>.r2.cloudflarestorage.com
BUCKET=logpush-appview
SINCE=$(date -u -v-24H '+%Y-%m-%dT%H')

aws s3 --endpoint-url "$R2_ENDPOINT" ls "s3://$BUCKET/" \
  | awk -v since="$SINCE" '$0 ~ since || $0 > since {print $4}' \
  | while read -r key; do
      aws s3 --endpoint-url "$R2_ENDPOINT" cp "s3://$BUCKET/$key" - \
        | gunzip -c
    done \
  | jq -r 'select(.Logs[]?.Message | test("\\[trust\\]\\[legacy\\] hit"))
           | .Logs[].Message
           | capture("matched=(?<m>true|false)").m' \
  | sort | uniq -c
```

**Pass criterion** — both counts (`matched=true` + `matched=false`) must
be **0** across the full 14-day window. A non-zero `matched=true`
indicates a straggler PDS that hasn't redeployed with
`applyViewerHeaders()`; trace by `did=` prefix in the same log line.
Any `matched=false` is a third-party client spoofing the legacy header
without the shared secret — expected to be 0 in production, but worth
investigating if it appears.

### Fallback — `wrangler tail` for an ad-hoc 5-minute probe

When Logpush is unavailable (e.g. during the cutover rehearsal before
the job is wired) use tail directly:

```bash
wrangler tail --format=json etzhayyim-appview \
  | jq -r 'select(.logs[]?.message[]? | test("\\[trust\\]\\[legacy\\] hit"))
           | .logs[].message[]' \
  | tee /tmp/legacy-trust-hits.log
```

Let it run for ≥ 5 minutes under normal load; grep the capture for
`hit did=` — expect zero lines on a healthy rollout.

## 3. Smoke test the HMAC-only path end-to-end in staging

Flip the flag on **staging** first. Verify:

```bash
cd 50-infra/cloudflare/workers/atproto
# Edit wrangler.jsonc — staging env block:
#   "LEGACY_TRUST_HEADERS": "off"
wrangler deploy --env staging

cd ../appview && wrangler deploy --env staging
cd ../chat && wrangler deploy --env staging
cd ../signal && wrangler deploy --env staging

# Smoke
ORIGIN=https://staging.atproto.etzhayyim.com bash 50-infra/cloudflare/workers/atproto/scripts/oauth-smoke.sh
# Per-Worker health
curl -sS https://staging.bsky.etzhayyim.com/_worker/health
curl -sS https://staging.chat.etzhayyim.com/_worker/health
curl -sS https://staging.signal.etzhayyim.com/_worker/health

# E2E: a logged-in call that hits AppView via PDS pipethrough
# (getAuthorFeed, getProfile). The viewer DID should round-trip even
# with no legacy headers on the wire.
etzhayyim authn signin
curl -sS "https://staging.atproto.etzhayyim.com/xrpc/app.bsky.feed.getAuthorFeed?actor=did:web:yoro.etzhayyim.com" \
  -H "Authorization: Bearer $(etzhayyim authn token)"
```

Run for ≥ 24h in staging before touching production.

# Flip procedure (T-0 production)

**Deploy order matters** — flip downstream Workers first so when PDS
stops emitting legacy headers the downstreams already reject them.
Anything in between is a brief window of legacy-accepting downstream +
HMAC-only upstream, which is the safe intersection.

```bash
# 1. bsky AppView first
cd 50-infra/cloudflare/workers/appview
# wrangler.jsonc: "LEGACY_TRUST_HEADERS": "off"
wrangler deploy

# 2. chat
cd ../chat
# wrangler.jsonc: "LEGACY_TRUST_HEADERS": "off"
wrangler deploy

# 3. signal
cd ../signal
# wrangler.jsonc: "LEGACY_TRUST_HEADERS": "off"
wrangler deploy

# 4. Finally the upstream PDS stops emitting legacy headers.
cd ../atproto
# wrangler.jsonc: "LEGACY_TRUST_HEADERS": "off"
wrangler deploy

# 5. Smoke
bash scripts/oauth-smoke.sh
# Expect: 22/22 unchanged. Viewer-identity-aware methods on the AppView
# (e.g. feed.getTimeline with viewer-specific muting) should still
# reflect caller identity.
```

# Rollback

Single env-var revert per Worker. Flip all four back to `"on"` and
redeploy **in reverse** (PDS first so it resumes emitting both header
sets, then downstream accepts either again):

```bash
cd 50-infra/cloudflare/workers/atproto
# wrangler.jsonc: "LEGACY_TRUST_HEADERS": "on"
wrangler deploy

cd ../appview && wrangler deploy
cd ../chat && wrangler deploy
cd ../signal && wrangler deploy
```

No data state change — trust caches are in-memory, redeploy clears
them. First post-rollback request pays the normal HMAC verify cost; no
user-visible break.

# Observability hooks

| Signal | Source | Threshold |
|---|---|---|
| HMAC verify reject rate | Worker Logpush, grep `[trust][verify] reject reason=` | < 0.1% of requests; spike = rollback. `reason=expired` vs `reason=bad_signature` tells you clock-skew vs secret-drift |
| Legacy-path hit count | Worker Logpush, grep `[trust][legacy] hit did=` | 0 events per 24h across 14d rolling window → safe to flip; any `matched=true` = straggler PDS, investigate by `did=` prefix |
| 401/403 spike on `/xrpc/*` | OCEL Analytics Engine, auth_level=public + status in [401, 403] | normal baseline + 2σ; spike = rollback |
| AppView getTimeline/getAuthorFeed viewer-aware shape | smoke E2E | authed fetch returns viewer-specific muting / thread state |
| Chat listConvos DID recognition | chat Worker HYPERDRIVE reads | viewer DID resolves, not anonymous |

# Post-flip cleanup (T+14d after flip)

Once `off` has run for 2 weeks without incident:

1. Remove the `LEGACY_TRUST_HEADERS` env var from all four wranglers.
2. Delete the legacy header-emission branches in
   `atproto/src/dispatch.ts` (grep for `emitLegacy` /
   `x-etzhayyim-authenticated-did` / `x-etzhayyim-internal-trust` — all should
   go).
3. Delete the legacy-verification branches in
   `appview/src/handlers/appview.ts` (the `allowLegacy` path and the
   `TRUSTED_VIEWER_DID_HEADER` / `INTERNAL_TRUST_HEADER` constants).
4. Same cleanup in chat + signal Workers once their real handlers
   (Phase δ2 / δ3 follow-up) land.
5. Update ADR-2604241038 with `status: active → active+γ2-complete` or
   mark the Phase γ2 line in the migration table as done.

# References

- ADR: `90-docs/adr/2604241038-yoro-pds-ideal-topology.md`
- Sibling runbook (DPoP cnf.jkt strict-mode): `90-docs/260424-oauth-strict-mode-cutover-runbook.md`
- Staging checklist: `90-docs/260424-oauth-appview-staging-deploy-checklist.md`
- Trust middleware: `50-infra/cloudflare/workers/atproto/src/middleware/trust.ts`
- Downstream verifier (reference): `50-infra/cloudflare/workers/appview/src/handlers/appview.ts`
