# Ingest Orchestration Design: Zeebe + Python on Kubernetes + MCP

**Status**: design accepted for implementation planning — 2026-04-25
**Scope**: all non-trivial ingest families: houbun/contracts, domain/common-crawl,
workspace, maps, patents, sanctions, media/news, talent, vehicles, ads, and
future public-data collectors.

## Decision

Use **Zeebe as the durable orchestration layer**, **Python workers on Kubernetes
as the source-specific execution layer**, and **MCP as the operator/agent control
surface**.

Kubernetes CronJobs may still exist, but only as **start signal emitters**:
they create Zeebe process instances and exit. They must not own cursor state,
retry policy, shard coordination, LLM analysis state, or final write semantics.

The default production shape is:

```text
MCP / XRPC / Cron trigger
        |
        v
bpmn-dispatcher -> Zeebe process instance
        |
        v
zeebe-worker / ingest-worker Python pods
        |
        +-- source APIs / object storage / local staging
        +-- LLM analysis through existing pymagatama.llm
        +-- graph writes through Kotoba/Datomic/Hyperdrive
        v
coverage reconciliation MVs + audit rows
```

## Placement Rules

Use Zeebe when an ingest has any of these properties:

- runs longer than five minutes
- has external API cursors, rate limits, shards, or pagination
- writes more than one graph table
- invokes LLM analysis or classification
- needs retry, incident replay, pause/resume, or human review
- must be observable as a durable run

Use Python-only Kubernetes Jobs only for bounded one-shot backfills where the
input and output are already fixed and the command can be restarted from a
deterministic cursor.

Use CronJob only for:

- creating scheduled Zeebe instances
- infrastructure maintenance such as backups
- health probes that do not mutate domain data

Do not add new long-running ingest logic to Cloudflare Workers. Workers remain
edge/auth/BFF and XRPC/MCP facades.

## Canonical Runtime Tables

Existing per-domain tables such as `vertex_workspace_cursor`,
`vertex_workspace_sync_job`, `vertex_maps_job`, `vertex_scraper_run`, and
`vertex_collector_run` remain valid. New cross-domain ingest state should use a
small shared spine:

```sql
CREATE TABLE vertex_ingest_run (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,

  run_id VARCHAR NOT NULL,
  ingest_family VARCHAR NOT NULL,      -- houbun, contracts, domain, maps, patent, ...
  source_id VARCHAR NOT NULL,          -- egov-jpn, govinfo-cfr, eurlex, uspto, ...
  mode VARCHAR NOT NULL,               -- delta, backfill, repair, verify
  status VARCHAR NOT NULL,             -- planned, running, paused, completed, failed, degraded

  zeebe_process_instance_key VARCHAR,
  bpmn_process_id VARCHAR,
  started_at VARCHAR,
  finished_at VARCHAR,
  requested_by VARCHAR,

  planned_shards BIGINT,
  completed_shards BIGINT,
  records_read BIGINT,
  records_written BIGINT,
  records_skipped BIGINT,
  error_count BIGINT,
  last_error VARCHAR,

  input_json VARCHAR,
  output_json VARCHAR,
  created_at VARCHAR
);

CREATE TABLE vertex_ingest_cursor (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,

  ingest_family VARCHAR NOT NULL,
  source_id VARCHAR NOT NULL,
  shard_key VARCHAR NOT NULL,
  cursor_value VARCHAR,
  cursor_hash VARCHAR,
  high_watermark VARCHAR,
  content_hash VARCHAR,
  updated_at VARCHAR,
  locked_by_run_id VARCHAR,
  lock_expires_at VARCHAR
);

CREATE TABLE vertex_ingest_artifact (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,

  run_id VARCHAR NOT NULL,
  artifact_kind VARCHAR NOT NULL,       -- raw, normalized, llm, error, coverage
  source_id VARCHAR NOT NULL,
  uri VARCHAR NOT NULL,                 -- b2://, s3://, at://, https:// evidence
  sha256 VARCHAR,
  byte_size BIGINT,
  record_count BIGINT,
  created_at VARCHAR
);
```

Domain-specific job tables may project into this spine by inserting one
`vertex_ingest_run` row per production run. The spine is for orchestration,
cursor ownership, and operator visibility; canonical domain facts still live in
domain tables such as `vertex_houbun_statute`, `vertex_open_patent_patent`,
`vertex_page`, or `vertex_workspace_raw_event`.

## Idempotency Contract

Every ingest worker must implement these rules:

- `vertex_id` is deterministic from source namespace + stable source id.
- `source_record_id` is preserved in the destination table when available.
- content hash is computed before write for large or mutable records.
- shard cursor advances only after write verification succeeds.
- retries re-read the same shard and overwrite the same deterministic rows.
- raw source evidence is stored or referenced before LLM-derived fields are
  written.
- LLM outputs are derived artifacts, never the only copy of source truth.

For Kotoba/Datomic degraded windows, a worker must run `rw.health.probe` or the
equivalent health gate before bulk writes. A successful client-side `INSERT`
result is not enough; post-write visibility checks drive cursor advancement.

## Zeebe Process Template

All ingest BPMN processes should follow this logical sequence:

```text
start
  -> health gate
  -> plan shards
  -> acquire shard lock
  -> fetch raw source
  -> persist raw artifact reference
  -> normalize records
  -> optional LLM analysis
  -> validate canonical rows
  -> write graph rows
  -> verify visibility / counts
  -> update cursor
  -> emit audit + coverage refresh hint
end
```

Retry behavior:

- fetch: retry with source-specific backoff and rate-limit handling
- normalize: fail fast to incident when parser changes break schema
- LLM: bounded retries, degraded path allowed only if destination marks
  `analysis_status='pending'`
- write: retry only after health gate passes
- verify: retry with delay, then mark run `degraded` instead of advancing cursor

## Python Worker Layout

Keep source-specific logic in `pymagatama.ingest.*` modules, not in operator
scripts. Operator scripts such as `70-tools/scripts/houbun_live_ingest.py` are
allowed as pilots, but production should call importable functions from Zeebe
task handlers.

Recommended package shape:

```text
20-actors/magatama/py/src/pymagatama/ingest/
  core.py             # run rows, cursor lock, artifact helpers, write verify
  houbun.py           # e-Gov, GovInfo, EUR-Lex, UN Treaty, Constitute Project
  contracts.py        # social contract projections
  domain.py           # local datasets + Common Crawl
  workspace.py        # Google / M365 sync wrappers
  maps.py             # OSM / Overpass / coverage targets
  patent.py           # USPTO / EPO
  media.py            # news, releases, entertainment
```

Zeebe task names should be stable and domain-scoped:

| Task type | Purpose |
|---|---|
| `ingest.plan` | create shards from source config |
| `ingest.acquireShard` | lock one shard/cursor |
| `ingest.fetch` | source-specific raw acquisition |
| `ingest.normalize` | source-specific parse to canonical rows |
| `ingest.llmAnalyze` | optional structured extraction/classification |
| `ingest.writeGraph` | deterministic graph writes |
| `ingest.verify` | count/read-after-write/coverage checks |
| `ingest.updateCursor` | cursor advancement |

The first implementation can register concrete task names such as
`houbun.egov.fetch`, `houbun.govinfoCfr.fetch`, and `patent.uspto.write`, then
converge to generic `ingest.*` once the shared input envelope stabilizes.

## Kubernetes

Add one production Deployment class for ingest workers:

```text
Deployment/ingest-worker
  command: python -m pymagatama.ingest_worker_main
  env:
    ZEEBE_GATEWAY
    KOTOBA_URL
    B2_* / source API credentials
    VULTR_SERVERLESS_KEY for LLM paths
  resources:
    small default CPU/memory
    per-family overrides for OCR/browser/heavy parse
```

Schedules become thin CronJobs:

```text
CronJob/ingest-houbun-delta
  -> python -m pymagatama.ingest_start --family houbun --source egov-jpn --mode delta

CronJob/ingest-domain-common-crawl
  -> python -m pymagatama.ingest_start --family domain --source common-crawl --mode delta
```

Heavy conversions such as patent PDF to webp/OCR remain separate specialized
Deployments, but report into `vertex_ingest_run` and `vertex_ingest_artifact`.

## MCP Surface

Expose ingest control through the Kysely-backed MCP registry
(`vertex_mcp_tool_def`), with lexicon/XRPC as the source contract.

Initial tools:

| Tool | Effect |
|---|---|
| `com.etzhayyim.apps.ingest.plan` | dry-run shard plan and estimated writes |
| `com.etzhayyim.apps.ingest.start` | create Zeebe process instance |
| `com.etzhayyim.apps.ingest.status` | read `vertex_ingest_run` and Zeebe keys |
| `com.etzhayyim.apps.ingest.pause` | mark run/cursors paused; Zeebe incident if active |
| `com.etzhayyim.apps.ingest.resume` | clear pause and retry incident/shard |
| `com.etzhayyim.apps.ingest.backfill` | bounded backfill with explicit source/range |
| `com.etzhayyim.apps.ingest.validate` | run visibility/count/source-hash checks |
| `com.etzhayyim.apps.coverage.refresh` | refresh or reconcile coverage read models |

MCP is an agent/operator facade. It does not become a second source of truth.
Lexicons define input/output contracts, BPMN defines orchestration, and
Kotoba/Datomic graph rows define durable state.

## Ingest Family Mapping

| Family | First source/process | Runtime |
|---|---|---|
| houbun/contracts | e-Gov JPN, Constitute, UNTC, GovInfo CFR, EUR-Lex | Zeebe + Python |
| domain/common-crawl | local datasets, Common Crawl intel/graph | Zeebe + existing TS/Python wrappers |
| workspace | Google Workspace, M365 | Zeebe + provider-specific Python |
| maps | OSM/Overpass/bootstrap coverage | Zeebe + existing K8s jobs |
| patent | USPTO PatentsView, EPO OPS, blob converter | Zeebe + Python + specialized converter pod |
| sanctions/company | OFAC/EU/UN lists, GLEIF | Zeebe + Python |
| media/news | feeds/releases/intel translation | Zeebe + Python + LLM |
| talent | occupations/job postings/BLS | Zeebe + Python |
| vehicles | NHTSA/EPA | Zeebe + Python |
| ads/scrapers | platform scrapers and browser artifacts | Zeebe + scraper/browser pods |

## Pilot Order

1. **houbun/contracts**: move the current live ingest pilot into
   `pymagatama.ingest.houbun`, add Zeebe task wrappers, and register one BPMN
   for `egov-jpn-delta` plus one for `world-law-backfill`.
2. **domain/common-crawl**: wrap the existing runbook commands behind
   `ingest.start` and `vertex_ingest_run`.
3. **patent**: reuse ADR-2604251024; register USPTO metadata and blob
   conversion as separate processes sharing `run_id`.
4. **workspace/maps**: bridge existing cursor/job tables into
   `vertex_ingest_run` without changing source semantics.

## Implementation Tasks

1. Add Kysely migration for `vertex_ingest_run`, `vertex_ingest_cursor`, and
   `vertex_ingest_artifact`.
2. Add lexicons for `com.etzhayyim.apps.ingest.{plan,start,status,pause,resume,backfill,validate}`.
3. Sync those lexicons into `vertex_mcp_tool_def`.
4. Add `pymagatama.ingest.core` with run/cursor/artifact helpers and
   read-after-write verification.
5. Move houbun pilot code from `70-tools/scripts/houbun_live_ingest.py` into
   importable worker functions.
6. Add `pymagatama.ingest_worker_main` or extend `zeebe_worker_main` with the
   initial ingest task registrations.
7. Add Kubernetes Deployment values for `ingest-worker`; keep the existing
   `zeebe-worker` for generic primitives.
8. Add BPMN process rows for houbun delta and world-law backfill.
9. Add a runbook: start, pause, resume, validate, and coverage reconciliation.

## Non-goals

- Replacing domain canonical tables with generic ingest tables.
- Making MCP the orchestration runtime.
- Moving edge auth or XRPC dispatch into Kubernetes.
- Treating one-off operator scripts as production schedulers.
