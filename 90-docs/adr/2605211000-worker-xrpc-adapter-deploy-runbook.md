# ADR-2605211000: Worker XRPC adapter deploy runbook (25 actors)

**Status**: ACTIVE
**Date**: 2026-05-21
**Decider**: Cloud Operator + Claude Opus 4.7

## Context

[ADR-2605210000](/90-docs/adr/2605210000-phase-e-reference-impl-completion.md) completed the rw-free reference implementation scaffold for all 25 actors. This ADR documents the execution-layer deploy procedure: wiring each rw-free package to a Cloudflare Worker, exposing XRPC endpoints, and smoke-testing.

Each actor has:
- `60-apps/etzhayyim-project-<actor>/xrpc-adapter/wrangler.jsonc` with route `<actor>.etzhayyim.com/xrpc/*`
- `src/index.ts` single-file XRPC dispatcher (imports rw-free functions)
- `package.json` with `@etzhayyim/sdk` + `@etzhayyim/<actor>-rw-free` workspace deps

## Deploy priority tiers

Operator deploys in strict order: Tier 1 → (wait 7 days) → Tier 2 → (wait 2 days) → Tier 3+4.

### Tier 1: Public read-only (deploy first, lowest risk)

**Actors** (7, CI matrix: `.github/workflows/test.yml` + `wrangler-validate.yml`): `isbn` / `gtin` / `ndc` / `houbun` / `hanrei` / `ipaddress` / `ocel`

> **open-isco excluded from xrpc-adapter cohort** (2026-05-21 reconciliation): the standalone CF Worker runtime is retired for open-isco (see `60-apps/etzhayyim-project-open-isco/CLAUDE.md` §"Active Runtime"). open-isco runs as BPMN + LangServer + LangGraph + UDF (`openIsco.classifyWorker` / `openIsco.recordConcordance`). The `@etzhayyim/open-isco-rw-free` package exists as a read-only embed surface (`queryByPrefix` / `getByCode` against `com.etzhayyim.apps.openIsco.occupation`) for other apps; no xrpc-adapter is shipped. Earlier drafts of this ADR listed open-isco at Tier 1; that was inconsistent with the BPMN-only runtime decision and is corrected here.

**Rationale**: No PII, no mutations from public callers, idempotent write path (rkey-gated, existing record check before write).

**Risk profile**:
- Read-only public APIs trivially recoverable (delete worker, restart from cache)
- Lexicon contracts stable (ISO standards, government registries)
- No user session required

### Tier 2: Closed-loop write (medium risk, internal/operator-only)

**Actors**: `sbom` / `kiyo` / `ki` / `koke` / `hakkou` / `houshi` / `houki` / `bpmn` / `dns`

**Rationale**: Internal/operator writes only (no ambient user session), no on-chain settlement (write path is PDS-only), deterministic rollback (rkey-direct delete).

**Risk profile**:
- Access-gated (operator credential or internal XRPC)
- Write idempotency = rkey-before-write (no dual-write), reversible (delete AT record)
- No cascading state dependencies (each actor isolated)

### Tier 3: User-state + workflow (higher risk, deploy after Tier 1+2 stable)

**Actors**: `otakiage` / `anime` / `manga` / `narou` / `gameka` / `yoro`

**Rationale**: User-generated content, state machines (otakiage certificate lifecycle, anime schedule), requires PDS session.

**Risk profile**:
- User session exposure (auth bearer token)
- State machine visibility (user sees partial progress during replay on revert)
- Rollback leaves user-visible orphaned records (mitigated by grace-period archival)

### Tier 4: Financial / sensitive (highest risk, gated on Tier 1+2 stability)

**Actors**: `open-banking` / `open-denki` / `isin`

**Rationale**: Ledger semantics (open-banking double-entry), critical infrastructure (open-denki grid ops), financial securities (isin).

**Risk profile**:
- Double-entry invariant (2 writes = atomic, PDS handles ordering)
- Grid fault response (open-denki signal/cancel = high-consequence)
- Securities metadata (isin compliance reporting)

Requires **7-day Tier 1+2 stability + post-incident review** before deploy approval.

## Pre-flight checklist (per actor)

Before `wrangler deploy`:

- [ ] rw-free package builds: `cd 60-apps/etzhayyim-project-<actor>/rw-free && npm ci && tsc` (exit 0)
- [ ] xrpc-adapter builds: `cd 60-apps/etzhayyim-project-<actor>/xrpc-adapter && npm ci && npm run build` (exit 0)
- [ ] `wrangler.jsonc` syntax: `npx wrangler publish --dry-run` (no errors)
- [ ] CF DNS record exists: `dig <actor>.etzhayyim.com` (CNAME to CF edge)
- [ ] PDS endpoint reachable: `curl https://pds.etzhayyim.com/xrpc/com.atproto.server.describeServer` (200)
- [ ] Env vars set in `wrangler.jsonc`: `ACTOR_DID`, `PDS_URL`, `L2_RPC_URL` (if applicable)

## Deploy command (per actor)

```bash
cd 60-apps/etzhayyim-project-<actor>/xrpc-adapter
wrangler deploy
# Cloudflare logs:
#   ✓ Uploaded <actor>-xrpc-adapter (256 KB)
#   ✓ Published to <actor>.etzhayyim.com
```

Example (Tier 1 first actor):

```bash
cd 60-apps/etzhayyim-project-isbn/xrpc-adapter
wrangler deploy
```

## Sanity check (per actor)

### Health endpoint (all actors)

```bash
curl -i https://<actor>.etzhayyim.com/xrpc/com.etzhayyim.<actor>.health
```

Expected response (200):

```json
{
  "status": "ready",
  "actor": "<actor>",
  "substrate": "pds",
  "timestamp": "2026-05-21T18:33:00Z"
}
```

### Write path test (per tier, first command)

**Tier 1 example (isbn — register book)**:

```bash
curl -X POST https://isbn.etzhayyim.com/xrpc/com.etzhayyim.isbn.registerBook \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <pds-session-token>' \
  -d '{
    "isbn13": "9784106102845",
    "title": "Example Book",
    "source": "openlibrary"
  }'
```

Expected response (200):

```json
{
  "status": "registered",
  "did": "did:web:isbn.etzhayyim.com#book-9784106102845",
  "bookUri": "at://did:web:isbn.etzhayyim.com/com.etzhayyim.isbn.book/rkey-…"
}
```

Or (if already exists):

```json
{
  "status": "alreadyExists",
  "error": "Book already registered under this rkey",
  "bookUri": "at://did:web:isbn.etzhayyim.com/com.etzhayyim.isbn.book/rkey-…"
}
```

**Tier 2 example (bpmn — deploy process)**:

```bash
curl -X POST https://bpmn.etzhayyim.com/xrpc/com.etzhayyim.bpmn.deployProcess \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <operator-token>' \
  -d '{
    "bpmnXml": "<?xml version=\"1.0\"?><bpmn:definitions ...></bpmn:definitions>",
    "processName": "example-workflow",
    "version": 1
  }'
```

Expected response (200):

```json
{
  "status": "deployed",
  "processId": "did:web:bpmn.etzhayyim.com#process-…",
  "uri": "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.bpmn.process/…"
}
```

**Tier 3 example (yoro — post to feed)**:

```bash
curl -X POST https://yoro.etzhayyim.com/xrpc/com.etzhayyim.yoro.postFeedItem \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <user-session-token>' \
  -d '{
    "text": "Hello, federation!",
    "facets": [],
    "reply": null,
    "embed": null
  }'
```

Expected response (200):

```json
{
  "status": "posted",
  "uri": "at://did:web:yoro.etzhayyim.com/com.etzhayyim.yoro.feedItem/…",
  "cid": "bagcqcer…"
}
```

**Tier 4 example (open-banking — record transaction)**:

```bash
curl -X POST https://open-banking.etzhayyim.com/xrpc/com.etzhayyim.open-banking.recordTransaction \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <user-session-token>' \
  -d '{
    "ledgerDid": "did:web:open-banking.etzhayyim.com#ledger-…",
    "debitAccount": "did:web:…#account-checking-123",
    "creditAccount": "did:web:…#account-savings-456",
    "amount": 50000,
    "amountCurrency": "usd",
    "description": "Transfer"
  }'
```

Expected response (200):

```json
{
  "status": "recorded",
  "uri": "at://did:web:open-banking.etzhayyim.com/com.etzhayyim.open-banking.transaction/…",
  "transactionId": "txn-…"
}
```

### List path test (sample aggregation, if applicable)

```bash
curl 'https://<actor>.etzhayyim.com/xrpc/com.etzhayyim.<actor>.list<Items>?limit=10&offset=0' \
  -H 'Authorization: Bearer <token>'
```

Expected response (200):

```json
{
  "records": [ {...}, ... ],
  "offset": 0,
  "limit": 10,
  "total": 1234,
  "truncated": false
}
```

## Regression check

Per root CLAUDE.md deploy checklist §3:

1. **PDS profile still loads**: `curl https://pds.etzhayyim.com/xrpc/app.bsky.actor.getProfile?actor=<actor>.etzhayyim.com` (200)
2. **subscribeRepos still fires**: `npm run test:firehose` or manual `subscribe-repos` client (see CI job) → no hang, new records appear
3. **No systematic 1101 errors**: `wrangler tail <actor>-xrpc-adapter --format json | grep 1101` (should be empty or transient retries only)

## Rollback procedure

### Per-actor rollback

If deploy introduces errors:

```bash
# Option 1: revert to previous published version
wrangler rollback --message "rollback to previous deployment"

# Option 2: delete worker entirely (safe — no data corruption)
wrangler delete <actor>-xrpc-adapter

# Option 3: manual revert via CF dashboard
# → Workers → <actor>-xrpc-adapter → Deployments → select previous → Promote
```

### Data safety

- **PDS records**: Hard delete only, no soft-delete. If rollback deletes worker, PDS records remain (idempotent re-register on worker re-deploy).
- **No cascading loss**: Each actor's records are isolated; reverting `<actor>` does not affect other actors.
- **Audit trail**: PDS firehose captures all writes; `subscribeRepos` replay is deterministic.

## Observability

### Live logs

```bash
wrangler tail <actor>-xrpc-adapter --format json | jq '.logs, .exceptions'
```

### Metrics (Cloudflare Logpush)

Workers deployed with `"observability": { "enabled": true }` in `wrangler.jsonc` automatically ship logs to Cloudflare logpush.

Configure destination:

```bash
# Example: ship to S3 bucket
wrangler logpush create --dataset workers_trace_events \
  --destination-conf "bucket=<bucket>,account-id=<account-id>" \
  --ownership-challenge <token>
```

Query recent errors:

```bash
# Cloudflare GraphQL
query {
  viewer {
    zones(filter: { names: "etzhayyim.com" }) {
      workersTraceEvents(limit: 100, filter: { where: { Status: "error" } }) {
        edges {
          node { Timestamp, Status, Exceptions }
        }
      }
    }
  }
}
```

## Phase F completion criteria

All 25 workers ready for production when:

- [ ] **All Tier 1 deployed + stable 7 days**: no errors > 1% of requests
- [ ] **All Tier 1 sanity checks pass**: health, write, list, regression
- [ ] **All Tier 2 deployed + stable 2 days**: access-gated, operator verified
- [ ] **All Tier 3 deployed after Tier 1+2 stable**: user session flows working
- [ ] **Tier 4 gated on post-incident review**: if any tier 1-3 fires alarm, tier 4 blocked until RCA + mitigation
- [ ] **Phase 3 mst-projector ADR drafted**: indexed views for search endpoints (ADR-2605211100, TBD)

## Related ADRs

- [ADR-2605210000](/90-docs/adr/2605210000-phase-e-reference-impl-completion.md) — Phase E rw-free scaffold completion
- [ADR-2605203000](/90-docs/adr/2605203000-rw-free-write-target-options.md) — rw-free write-target options (foundation)
- [ADR-2605172000](/90-docs/adr/2605172000-etzhayyim-rw-free-substrate.md) — RW-free substrate mandate
- [ADR-2605172400](/90-docs/adr/2605172400-etzhayyim-vendor-three-axis-split-rule.md) — Vendor/etzhayyim 3-axis split
