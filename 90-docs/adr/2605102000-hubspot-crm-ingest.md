---
id: hubspot-crm-ingest
title: "ADR-2605102000: HubSpot CRM Ingest Facade"
status: active
doc_type: adr
topic: hubspot-crm-ingest
authoritative: true
last_verified: 2026-05-10
authoritative_for:
  - HubSpot CRM v3 ingest worker design
  - vertex_hubspot_* schema
  - HubSpot Private App auth topology
related:
  - worker-direct-hyperdrive-persistence
  - simplified-3layer-identity-rw-vault
---

# ADR 2605102000 — HubSpot CRM Ingest Facade

**Date**: 2026-05-10
**Status**: accepted (scaffold + token issued; RW apply + deploy pending y-nishino)
**Operator**: etzhayyim
**Implementer (this iteration)**: Claude on behalf of CEO 河崎 (etzhayyim agent execution-phase)

## Context

CEO 河崎 directive 「hubspot のデータを全て kotoba に取り込んで」 (DECISION-LOG iter 123, 127).
Existing 1Password entry `op://Private/Hubspot` was Microsoft-SSO login only — no API
token. No prior HubSpot ingest worker existed. Closest precedent (`open-sales` actor,
ADR 2604281830) is a HubSpot-equivalent self-CRM, not an ingest pipeline.

## Decision

Build a single TS-Native CF Worker (`hubspot.etzhayyim.com`, nanoid `hb5p0t1n`,
did:web:hubspot.etzhayyim.com) that polls HubSpot CRM v3 REST API and writes each row
to `vertex_hubspot_*` via Hyperdrive direct per ADR-0036. Surface 4 NSIDs over
XRPC + auto-published MCP:

- `com.etzhayyim.apps.hubspot.syncObjectType` — incremental sync for one object type
- `com.etzhayyim.apps.hubspot.syncAll` — fan-out over all 8 types (cron entrypoint)
- `com.etzhayyim.apps.hubspot.listObjects` — read-side projection
- `com.etzhayyim.apps.hubspot.getSyncStatus` — sync cursor inspection

## Object coverage (8 types)

| Object | HubSpot endpoint | Table |
|---|---|---|
| contact | `/crm/v3/objects/contacts/search` | `vertex_hubspot_contact` |
| company | `/crm/v3/objects/companies/search` | `vertex_hubspot_company` |
| deal | `/crm/v3/objects/deals/search` | `vertex_hubspot_deal` |
| ticket | `/crm/v3/objects/tickets/search` | `vertex_hubspot_ticket` |
| owner | `/crm/v3/owners` (list, no search) | `vertex_hubspot_owner` |
| engagement | 5-subtype fan-out: `/crm/v3/objects/{calls,emails,meetings,notes,tasks}/search` | `vertex_hubspot_engagement` (`engagement_type` discriminator) |
| lineItem | `/crm/v3/objects/line_items/search` | `vertex_hubspot_line_item` |
| product | `/crm/v3/objects/products/search` | `vertex_hubspot_product` |

Plus `vertex_hubspot_sync_cursor` for per-object `hs_lastmodifieddate` watermark.

## Schema discipline

Per `30-graph/graph-schema/CLAUDE.md` + root `CLAUDE.md` Record-log semantics:

- All columns are `varchar` / `bigint` / `date` / `double precision` (no JSON, no float).
- Promoted columns for high-frequency fields; raw fanout in `properties_json` (varchar).
- Append-only PK re-INSERT = implicit upsert. **No `ON CONFLICT` (Kotoba/Datomic parser rejects).**
- Hard-delete only (`_alive` soft-delete forbidden).
- 4 RLS canonical columns (`actor_did`, `org_did`, `at_did`, `created_at`) per ADR-0095.
- `sensitivity_ord = 3` (PII Tier 3) — HubSpot data contains contact PII.

## Auth + secret topology

- HubSpot Legacy Private App `etzhayyim-kotoba-ingest`, App ID `39124460`, portal `42189574`.
- 18 read scopes: `crm.objects.{contacts,companies,deals,owners,line_items,products,quotes,subscriptions,feedback_submissions}.read` + `crm.schemas.{contacts,companies,deals,line_items,quotes,subscriptions}.read` + `tickets` + `e-commerce` + `sales-email-read`.
- Token stored in 3 locations:
  1. macOS Keychain (`etzhayyim.hubspot/HUBSPOT_PRIVATE_APP_TOKEN`)
  2. `~/.etzhayyim/hubspot.env` (chmod 600)
  3. CF Secrets Store secret `a327ccfaec7f4b859bda2bc1321ac8c8` in store `1824561668fe47cc9127d493961885af` as `hubspot_private_app_token`
- Worker binds via `SS_HUBSPOT_PRIVATE_APP_TOKEN`.

## Why Legacy Private App (not new MCP-Auth-App or Service Key)

- HubSpot deprecated the standalone Private Apps page 2026-Q2; `MCP認証アプリ` and Service Keys are the new alternatives.
- Service Keys pair with HubSpot Developer Projects (different scope set, different lifecycle); not yet validated against the v3 REST endpoints used here.
- `MCP認証アプリ` targets MCP servers consumed by HubSpot's own AI features — orthogonal to our server-side polling pattern.
- Legacy Private App still works for `Authorization: Bearer <token>` on `/crm/v3/objects/*` and is the verified-working path. Future migration to Service Keys is a 1-secret swap.

## Cadence

R/PT15M timer (Zeebe BPMN, L7) → `syncAll {maxPagesPerType: 50}`.
Initial backfill: `syncAll {since: "1970-01-01T00:00:00Z", maxPagesPerType: 200}`.

## Layer placement

| Layer | Component |
|---|---|
| L2 Routing | atproto.etzhayyim.com PDS XRPC entry |
| L3 Dispatcher | `hubspot.etzhayyim.com` Worker (this ADR) |
| L4 Registry | `vertex_capability` MCP tool definitions auto-registered on first hit |
| L5 Storage | Kotoba/Datomic Hummock (B2) `vertex_hubspot_*` |
| L7 Orchestration | Zeebe R/PT15M timer for `syncAll` cron |

## Pending

- y-nishino: apply alembic head `r_20260510010000_vertex_hubspot` to RW (network-unreachable from claude host).
- y-nishino: `etzhayyim deploy` from `60-apps/etzhayyim-project-hubspot-hb5p0t1n/appview/etzhayyim-wasm-hubspot-hb5p0t1n/`.
- y-nishino: trigger initial backfill via XRPC `syncAll`.
- Future: derive rules from `vertex_hubspot_deal` → `vertex_keiei_decision` (CXO graph, ADR 2605101200) for capital-flow grounding.

## Files

- `30-graph/graph-schema/sql_migrations/20260510010000_vertex_hubspot.{up,down}.sql`
- `30-graph/graph-schema/alembic/current_versions/r_20260510010000_vertex_hubspot.py`
- `00-contracts/lexicons/com/etzhayyim/apps/hubspot/{syncObjectType,syncAll,listObjects,getSyncStatus}.json`
- `60-apps/etzhayyim-project-hubspot-hb5p0t1n/appview/etzhayyim-wasm-hubspot-hb5p0t1n/{kotodama.jsonld,wrangler.jsonc,package.json,tsconfig.json,src/app.ts}`
- `_working/etzhayyim-revenue/DECISION-LOG.md` iter 123, 127
