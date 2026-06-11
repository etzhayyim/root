---
id: adr-2605130900-crm-open-lei-bridge-review-loop
title: "ADR-2605130900: CRM Open LEI Bridge Review Loop"
status: accepted
doc_type: adr
topic: crm-open-lei-bridge
authoritative: true
last_verified: 2026-05-13
authoritative_for:
  - CRM to Open LEI graph bridge
  - lawfirm and HubSpot LEI enrichment columns
  - Open LEI MCP review and evidence workflow
  - LangGraph-assisted LEI human review queue
related:
  - adr-2604281830-open-sales-crm-actor
  - hubspot-crm-ingest
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605080400-alembic-scope-contract
---

# ADR-2605130900 - CRM Open LEI Bridge Review Loop

## Context

Salesforce / HubSpot alternatives in this repo are graph-native CRM surfaces:
`open-sales`, `lawfirm`, and the HubSpot ingest facade. They already store lead,
tenant, and company rows in Kotoba/Datomic, but external legal-entity grounding was
not consistently represented.

Open LEI data exists in `vertex_open_lei_entity`; the missing layer was a
reversible bridge from CRM rows to LEI entities, with enough review state to
avoid falsely verifying ambiguous law firm names.

## Decision

Add a graph bridge between CRM vertices and Open LEI vertices.

Schema:

- Add LEI match columns to `vertex_lawfirm_lead`, `vertex_lawfirm_tenant`, and
  `vertex_hubspot_company`.
- Add `edge_crm_open_lei_match` for candidate / verified / rejected links.
- Add `vertex_crm_lei_resolution_run` for resolver runs.
- Add `vertex_crm_lei_review_item` as the human review queue.
- Add `view_crm_lei_pending_resolution`, `view_crm_lei_linked_entity`,
  `view_crm_lei_review_queue`, and `mv_crm_lei_coverage`.

Runtime:

- Extend `50-infra/k8s/open-lei-mcp/mcp_server.py` with
  `openLei.crm.bridge.*` tools:
  `query`, `resolve`, `review`, `autoreview`, `enrich`, `reviewQueue`, and
  `submitEvidence`.
- Use deterministic exact / normalized / fuzzy candidates, but only move a row
  to `verified` through explicit allowlisted auto-review or human
  `verify_selected_lei`.
- Keep `submitEvidence` review-local: it updates queue evidence and regenerated
  candidates, but does not mutate the CRM source row.

## Consequences

CRM rows can now be linked to Open LEI entities without losing provenance or
over-writing weak matches. Ambiguous entities remain reviewable. This matters
for Indian law firm leads where names are often partner-style, LLP-style, or
brand-style and where Open LEI may contain multiple similar registrations.

As of 2026-05-13:

- Verified bridge edges: 8.
- Remaining Indian lawfirm review rows: 5, all `needs_human_review` with
  evidence URI attached.
- `sr-2026` has multiple normalized exact `S R ASSOCIATES` candidates and must
  be resolved by human selected-LEI review, not auto-verification.
- `pnpm db:drift` from `30-graph/graph-schema` reports no drift.

## Implementation Files

- `30-graph/graph-schema/sql_migrations/20260512110000_crm_open_lei_bridge.up.sql`
- `30-graph/graph-schema/sql_migrations/20260512110000_crm_open_lei_bridge.down.sql`
- `30-graph/graph-schema/alembic/current_versions/r_20260512110000_crm_open_lei_bridge.py`
- `30-graph/graph-schema/sql_migrations/20260512140000_crm_lei_review_queue.up.sql`
- `30-graph/graph-schema/sql_migrations/20260512140000_crm_lei_review_queue.down.sql`
- `30-graph/graph-schema/alembic/current_versions/r_20260512140000_crm_lei_review_queue.py`
- `50-infra/k8s/open-lei-mcp/mcp_server.py`
- `50-infra/k8s/open-lei-mcp/README.md`
- `00-contracts/lexicons/com/etzhayyim/apps/crm/resolveLei.json`
- `00-contracts/lexicons/com/etzhayyim/apps/crm/listLeiLinks.json`
- `00-contracts/lexicons/com/etzhayyim/apps/crm/listLeiPending.json`
- `00-contracts/lexicons/com/etzhayyim/apps/crm/reviewLei.json`
- `00-contracts/lexicons/com/etzhayyim/apps/crm/autoreviewLei.json`
- `00-contracts/lexicons/com/etzhayyim/apps/crm/enrichLeiReviewQueue.json`
- `00-contracts/lexicons/com/etzhayyim/apps/crm/listLeiReviewQueue.json`
- `00-contracts/lexicons/com/etzhayyim/apps/crm/reviewLeiQueue.json`
- `00-contracts/lexicons/com/etzhayyim/apps/crm/submitLeiEvidence.json`

## Closing State

Use `openLei.crm.bridge.query` with `mode=review` or
`openLei.crm.bridge.reviewQueue` to continue. The next required action is
human selection for the 5 review rows, especially `sr-2026`.

Do not mark `reject_candidates` rows as `no_match` merely because the current
candidate set is weak; `reject_candidates` means "needs better evidence".
