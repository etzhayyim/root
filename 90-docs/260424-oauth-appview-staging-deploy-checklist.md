---
id: doc-260424-oauth-appview-staging-deploy-checklist
title: "OAuth + AppView staging deploy checklist (ADR-2604231821 / 2604231828 / 2604240914)"
status: active
doc_type: how-to
topic: deploy-checklist
authoritative: true
last_verified: 2026-04-24
authoritative_for:
  - post-merge deploy order for atproto / authn / bsky Workers
  - ADR-2604231821 / 2604231828 / 2604240914 cutover smoke steps
related:
  - adr-2604231821-atproto-oauth-wire-format-snake-case
  - adr-2604231828-appview-domain-separation-bsky-etzhayyim-ai
  - adr-2604240914-oauth-rs-binding-revocation-introspection
  - doc-260424-oauth-strict-mode-cutover
---

# Context

This session landed:

| Commit | Scope |
|---|---|
| `cf5b0ecfb69` | OAuth wire format snake_case (AS metadata / PAR / token / client metadata) |
| `3c88a7dff38` | DPoP-Nonce on `/oauth/token` + authn response snake_case |
| `12e119b3a19` | `etzhayyim-appview` Worker scaffold |
| `988f0614a35` | `APPVIEW_URL` var in atproto wrangler |
| `70536e55b18` | PDS pipethrough public HTTP + RS DPoP middleware |
| `0cbfcfd3845` | `cnf.jkt` through session JWT + `/oauth/revoke` + AppView proxy |
| `5c8667d2cb6` | RS revocation lookup + `/oauth/introspect` |
| `f31a2925a4e` | Y2 B3 family cascade + `DPOP_CNF_JKT_ENFORCEMENT` switch |
| `c38e4ada5a3` | smoke script + runbook + `etzhayyim authn revoke` |
| `{next}`     | **AppView A2 full migration + package.json wiring** |

Current prod baseline (against live `atproto.etzhayyim.com`):

```
$ bash 50-infra/cloudflare/workers/atproto/scripts/oauth-smoke.sh
  pass: 17
  fail: 5    # revoke + introspect endpoints + their AS metadata fields
```

The 5 fails clear once the atproto Worker redeploys with commit
`f31a2925a4e` or later.

# Deploy order

Deploy **authn first**, then **bsky (AppView)**, then **atproto PDS**. This
keeps each Worker's dependencies hot before the next one starts relying on
them, and lets rollback be one-Worker granular if a stage fails smoke.

## 1. authn.etzhayyim.com (authentication service)

```bash
cd 60-apps/etzhayyim-project-auth/worker
wrangler deploy
```

**Ships**:
- `/oauth/token` response snake_case (Phase 3 S5)
- `cnf.jkt` propagation in `issueSession` / `refreshSession` (Y1 A2)
- `sid` (session-family id) on both access and refresh JWTs (Y2 B3)
- New `/rpc/revoke-token` + `/rpc/check-revoked` (Y2 B1, B2)
- `vertex_etzhayyim_key_revoked_session.sid` column migration (idempotent
  ALTER TABLE — safe to re-run)

**Smoke**:

```bash
# AS-side (still lives on authn): JWKS present
curl -sS https://authn.etzhayyim.com/.well-known/jwks.json | jq '.keys | length'
# expect: ≥ 1
```

## 2. bsky.etzhayyim.com (Layer 2 AppView)

```bash
cd 50-infra/cloudflare/workers/appview
pnpm install   # workspace deps (@etzhayyim/graph-schema, @etzhayyim/kotodama-host-sdk, kysely, pg)
wrangler deploy
```

**Ships**:
- Worker scaffold on `bsky.etzhayyim.com/*`
- Real `app.bsky.{actor,feed}.*` handlers migrated from yoro
  (`profile`/`search`/`feed`/`rank`/`intent-prior`/`topic-extract`)
- `x-etzhayyim-internal-trust` gate on `x-etzhayyim-authenticated-did` forwarding

**Smoke**:

```bash
# Health probes
curl -sS https://bsky.etzhayyim.com/_worker/health
# expect: {"ok":true,"app":"appview",...}

curl -sS https://bsky.etzhayyim.com/_app/meta
# expect: {"app":"etzhayyim-appview","layer":"appview","atStandard":true,...}

# Unknown NSID → 501 (PDS will fall back to local handler)
curl -sS -o /dev/null -w "%{http_code}\n" https://bsky.etzhayyim.com/xrpc/app.bsky.feed.getCustomFeed
# expect: 501

# Migrated NSID → 200 + JSON body
curl -sS "https://bsky.etzhayyim.com/xrpc/app.bsky.actor.getProfile?actor=did:web:yoro.etzhayyim.com" | jq .did
# expect: a DID string

# Non-app.bsky.* rejection
curl -sS -o /dev/null -w "%{http_code}\n" https://bsky.etzhayyim.com/xrpc/com.atproto.repo.listRecords
# expect: 501
```

## 3. atproto.etzhayyim.com (PDS + Entryway)

```bash
cd 50-infra/cloudflare/workers/atproto
# If APPVIEW_INTERNAL_SECRET is not yet provisioned (optional — bsky
# will accept viewer DID claims without the secret during migration):
#   wrangler secret-store-secret put 1824561668fe47cc9127d493961885af \
#     --name appview_internal_trust --scopes workers --remote
wrangler deploy
```

**Ships**:
- `revocation_endpoint` + `introspection_endpoint` in AS metadata
- `POST /oauth/revoke` + `POST /oauth/introspect`
- `dpopResourceServerMiddleware` on `/xrpc/*` (nonce enforce + Y1 A3
  warn-mode `cnf.jkt` matching)
- `pipethroughAppView` switched to `fetch(APPVIEW_URL)` (public HTTP)
- RS-side `isJtiRevoked` blacklist lookup in `verifyServiceAuthJWT`
- Default `DPOP_CNF_JKT_ENFORCEMENT=warn` (strict-mode flip later —
  see `260424-oauth-strict-mode-cutover-runbook.md`)

**Smoke**:

```bash
bash scripts/oauth-smoke.sh
# expect: pass: 22, fail: 0
```

Extra end-to-end check:

```bash
# Revoke → introspect round-trip. sk_live_* from `etzhayyim authz list-api-keys`.
SK=$(security find-generic-password -s "etzhayyim.dev" -a "sk_live" -w 2>/dev/null || echo "$etzhayyim_API_KEY")
# 1. mint a session via passkey login (browser)
etzhayyim authn signin

# 2. revoke it server-side
etzhayyim authn revoke -q

# 3. introspect the revoked token with a confidential client
TOK=$(jq -r .access_token ~/.etzhayyim/auth.json.bak 2>/dev/null)   # or capture before revoke
curl -sS -X POST https://atproto.etzhayyim.com/oauth/introspect \
  -H "Authorization: Bearer $SK" \
  -d "token=$TOK" | jq .
# expect: {"active": false}
```

# Rollback

Each Worker rollbacks independently via `wrangler rollback`:

```bash
wrangler rollback --message "revert ADR-2604240914 pass"
```

- atproto Worker rollback: `/oauth/revoke` + `/oauth/introspect` go 404,
  AS metadata drops `revocation_endpoint` / `introspection_endpoint`.
  RS DPoP middleware unwires → DPoP scheme falls through as before.
  Pipethrough falls back to local (since `APPVIEW_URL` still works with
  the bsky Worker serving).
- bsky Worker rollback: bsky.etzhayyim.com returns 501 for every NSID →
  atproto PDS falls back to local handlers (yoro-side copy still in
  place as safety net). Net effect: same as pre-migration.
- authn Worker rollback: session issuance drops `cnf.jkt` + `sid`
  claims; RS gracefully skips revocation lookups for sid-less tokens.

Cache side effects: all rollbacks clear the Worker's in-memory caches
(`_dpopJtiCache`, `_dpopNonceCache`, `_jtiRevocationCache`,
`_apiKeyCache`). First request to rollback-Worker gets fresh state.

# Post-deploy watch

```bash
# Tail Logpush for unexpected warn/error spikes.
# Replace with tenant-specific query.
jq -r '.timestamp, .message' atproto-*.jsonl \
  | grep -E "(dpop/rs|oauth/revoke|oauth/introspect|auth/revoke)" \
  | head -50
```

Signals to watch the first 24h:

| Signal | Expected | Alert if |
|---|---|---|
| `[dpop/rs] access token missing cnf.jkt (grace)` | rising briefly as legacy tokens cycle out, then → 0 within 15m (access_token TTL) | sustained > 1/min after 1h |
| `[dpop/rs] cnf.jkt ↔ proof jkt mismatch (grace)` | 0 | any occurrence |
| `[oauth/token] DPoP proof verification failed` | 0 during normal flows | recurring on same client |
| `[auth/revoke] AUTH_SERVICE unavailable, fail-open` | 0 | any sustained rate |

# References

- Smoke: `50-infra/cloudflare/workers/atproto/scripts/oauth-smoke.sh`
- Strict-mode runbook: `90-docs/260424-oauth-strict-mode-cutover-runbook.md`
- ADRs: `90-docs/adr/2604231821-*.md`, `90-docs/adr/2604231828-*.md`, `90-docs/adr/2604240914-*.md`
