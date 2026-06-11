---
id: doc-260427-state-worker-retirement-session-summary
title: "Session summary: state CF Worker retirement via Zeebe/k8s/Kotoba/Datomic gates"
status: active
doc_type: reference
topic: state-worker-retirement
authoritative: false
last_verified: 2026-04-27
related:
  - adr-2604262000-edge-thin-app-runtime-k8s-zeebe-registry
  - adr-2604261000-mcp-registry-via-kysely-schema
  - adr-2604261900-kotoba-ddl-backfill-path-topology
  - doc-260426-site-common-crawl-zeebe-python-worker-design
---

# Scope

Session record for the first country-state Cloudflare Worker retirements under
ADR-2604262000. The goal was to prove that app actors can leave per-country
Cloudflare Workers and run through MCP registry, BPMN/Zeebe, Kubernetes Python
workers, Kotoba/Datomic, and B2 evidence instead.

# Completed

## AFG

- Worker `kotodama-g0vafg01` was deleted after its k8s/BPMN/RW coverage gate
  was green.
- No rollback was required.

## ZAF

- Worker `kotodama-g0vzaf01` was deleted from Cloudflare.
- Post-delete Cloudflare check returned `This Worker does not exist on your
  account [10007]`, confirming deletion.
- Routes retired with the Worker:
  - `g0vzaf01.etzhayyim.com/*`
  - `zaf-state.etzhayyim.com/*`

ZAF replacement path:

- Python Zeebe worker module: `kotodama.primitives.gov_zaf`.
- BPMN contracts: `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/govZaf/*.bpmn`.
- Lexicons: `00-contracts/lexicons/com/etzhayyim/govZaf/*.json`.
- Registry migration:
  `30-graph/graph-schema/migrations/20260426230000_seed_gov_zaf_bpmn_mcp_registry.ts`.
- Official-source coverage migration:
  `30-graph/graph-schema/migrations/20260427010000_seed_gov_zaf_official_source_coverage.ts`.
- Coverage verifier:
  `30-graph/graph-schema/scripts/verify-gov-zaf-coverage.mjs`.

Official source basis:

- South African Government national departments:
  `https://www.gov.za/about-government/government-system/national-departments`
- South African Government provinces:
  `https://www.gov.za/provinces`
- South African Government provincial government links:
  `https://www.gov.za/links/provincial-government`

Final gate:

```text
npm run verify:gov-zaf
ok: true
deleteAllowed: true
page: 3/3
wet: 3/3
wat: 3/3
screenshot: 3/3
govSources: 3/3
orgSeeds: agency=11 ministry=33 state=9
```

# Kotoba/Datomic Index Fix

`vertex_page` lookups initially timed out because the table had no visible
index and point lookups were scanning a ~985M-row table. The ZAF gate now relies
on a narrow covering index:

```sql
CREATE INDEX IF NOT EXISTS idx_vertex_page_vertex_id_cover
ON vertex_page(vertex_id)
INCLUDE (rkey, url, domain, title, status_code, content_type)
DISTRIBUTED BY (vertex_id);
```

Migration:

- `30-graph/graph-schema/migrations/20260427013000_index_vertex_page_vertex_id_cover.ts`

The background DDL completed. `EXPLAIN` now plans ZAF page lookups against
`idx_vertex_page_vertex_id_cover`, not `vertex_page`.

Operational note: the backfill hit Backblaze B2 `SlowDown`/temporary read
errors during compaction, but Kotoba/Datomic retried and completed. Future large
indexes must use narrow covering shapes and background DDL, and should be
monitored through `SHOW JOBS`, `SHOW INDEXES`, and `EXPLAIN`.

# Current Retired State Workers

| country | worker | status | deletion evidence |
|---|---|---|---|
| AFG | `kotodama-g0vafg01` | deleted | prior green gate + successful delete |
| ZAF | `kotodama-g0vzaf01` | deleted | Cloudflare API reports Worker missing |
| AGO | `kotodama-g0vago01` | deleted | Cloudflare API reports Worker missing |

# Next Candidate

Candidate selected for the next one-by-one migration: Angola.

Worker:

- `kotodama-g0vago01`
- routes:
  - `g0vago01.etzhayyim.com/*`
  - `ago-state.etzhayyim.com/*`
- local path:
  `60-apps/etzhayyim-project-states/appview/etzhayyim-wasm-states-ago-g0vago01`

Official-source anchors selected for AGO:

- Ministers list: `https://governo.gov.ao/ministro`
- Provincial governors list: `https://governo.gov.ao/governador`
- Provinces table: `https://governo.gov.ao/angola/provincias`

Implementation started:

- Python Zeebe worker module: `kotodama.primitives.gov_ago`.
- BPMN contracts: `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/govAgo/*.bpmn`.
- Lexicons: `00-contracts/lexicons/com/etzhayyim/govAgo/*.json`.
- Registry migration:
  `30-graph/graph-schema/migrations/20260427113000_seed_gov_ago_bpmn_mcp_registry.ts`.
- Official-source coverage placeholder migration:
  `30-graph/graph-schema/migrations/20260427114000_seed_gov_ago_official_source_coverage.ts`.
- Coverage verifier:
  `30-graph/graph-schema/scripts/verify-gov-ago-coverage.mjs`.

Seed coverage now tracks the current official Angola government portal shape:
24 ministry rows from the `Ministros` page and 21 province rows from the
`Governadores Provinciais` page, including Icolo e Bengo, Moxico Leste,
Cuando, and Cubango.

AGO deletion sequence:

1. applied the AGO BPMN/MCP registry migration to Kotoba/Datomic;
2. registered the Python Zeebe worker surface through `gov_ago`;
3. ingested page/WET/WAT/gyotaku evidence for the three official pages;
4. ran `pnpm --dir 30-graph/graph-schema verify:gov-ago`;
5. confirmed Cloudflare deployment existed;
6. deleted `kotodama-g0vago01`;
7. confirmed Cloudflare API reports the Worker missing;
8. re-ran `verify:gov-ago` after deletion.

Update after implementation:

- The two AGO migrations were applied from Apple Keychain
  `etzhayyim.rw/ROOT_URL`:
  - `20260427113000_seed_gov_ago_bpmn_mcp_registry`
  - `20260427114000_seed_gov_ago_official_source_coverage`
- Drift check passed and `30-graph/graph-schema/src/database.ts` was
  regenerated by the migration helper.
- `gov_ago.task_gov_ago_seed_orgs(limit=100)` seeded 45 rows:
  24 ministry rows and 21 state/province rows.
- `site.etzhayyim.com` ingest returned Cloudflare 522 from the site origin, so the
  fallback script
  `70-tools/scripts/gov/ingest-gov-ago-official-sources.py` captured the three
  official pages directly, uploaded HTML + gyotaku PNG evidence to B2, and
  wrote `vertex_page`, `vertex_wet_chunk`, `vertex_wat`, and
  `vertex_screenshot`.

Final AGO gate:

```text
pnpm --dir 30-graph/graph-schema verify:gov-ago
ok: true
deleteAllowed: true
page: 3/3
wet: 3/3
wat: 3/3
screenshot: 3/3
govSources: 3/3
orgSeeds: ministry=24 state=21
```

AGO deletion result:

- `pnpm exec wrangler delete kotodama-g0vago01 --force` completed
  successfully.
- Post-delete Cloudflare check returned `This Worker does not exist on your
  account [10007]`.
- Post-delete `verify:gov-ago` remained green with `deleteAllowed: true`.

# Session Close State

- Do not delete any further state Worker without a green coverage verifier.
- `vertex_page` point lookup performance blocker is resolved for `vertex_id`
  reads.
- Existing unrelated dirty files in the worktree were not touched.
