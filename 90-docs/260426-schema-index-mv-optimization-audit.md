# Kotoba/Datomic Schema Index and MV Naming Audit

Date: 2026-04-26 JST

## Live Findings

The live Kotoba/Datomic catalog has:

- `vertex_*`: 1213 tables, all `table`
- `edge_*`: 332 tables, all `table`
- `mv_*`: 244 materialized views and 2 plain views

No `vertex_*` or `edge_*` relation is a view/materialized view. That convention
is healthy.

Two `mv_*` names are plain views:

- `mv_maps_coverage_gap_ranked`
- `mv_world_coverage_live`

`mv_maps_coverage_gap_ranked` is a stale compatibility alias. The canonical name
is already `view_maps_coverage_gap_ranked`.

`mv_world_coverage_live` is currently a plain view because
`20260426203000_gov_dedup_denominator_runtime.ts` changed the final world
coverage layer from MV to runtime view. Many readers still query this legacy
name, so the next migration adds `view_world_coverage_live` as the canonical
alias without dropping `mv_world_coverage_live`.

## Index Coverage

Secondary index coverage is sparse:

- `vertex_*`: 986 / 1213 tables have no secondary index
- `edge_*`: 255 / 332 tables have no secondary index

The next safe migration adds indexes for bounded tables and projection paths:

- `vertex_maps_coverage_target(source_did, label)`
- `vertex_maps_coverage_target(last_fetched_at)`
- `vertex_contracts_organization(source_record_id)`
- `vertex_open_lei_entity(lei)`
- `vertex_open_lei_entity(country, status)`
- `vertex_open_lei_ownership(parent_lei)`
- `vertex_open_lei_ownership(child_lei)`
- `edge_open_lei_ownership_pair(src_vid)`
- `edge_open_lei_ownership_pair(dst_vid)`
- observed LEI-bearing domain tables such as `edge_hospitality_lei_bridge(lei)`
  and `vertex_real_estate_party(lei)`

## Heavy DDL Queue

Do not apply the following from a migration runner or hot-path worker:

```sql
CREATE INDEX IF NOT EXISTS idx_vertex_legal_entity_lei
  ON vertex_legal_entity (lei);
```

`vertex_legal_entity` is 100M+ rows in live Kotoba/Datomic. The 2026-04-26
`intel.entity.resolve` timeout was caused by an unindexed LEI lookup against
this table. The index is valid, but it must be submitted through the serialized
Kotoba/Datomic DDL queue:

```sql
SET BACKGROUND_DDL = true;
SET streaming_parallelism_strategy_for_index = 'BOUNDED(1)';
CREATE INDEX IF NOT EXISTS idx_vertex_legal_entity_lei
  ON vertex_legal_entity (lei);
SET BACKGROUND_DDL = false;
```

Monitor with:

```sql
SELECT * FROM rw_catalog.rw_ddl_progress;
SHOW JOBS;
WAIT idx_vertex_legal_entity_lei;
```

Only one heavy DDL job should run at a time. Do not run concurrent `COUNT(*)`
or MV rebuilds against the same large table during the backfill.

### 2026-04-26 Live Attempt

Attempted `idx_vertex_legal_entity_lei` through the manual DDL queue path:

- job id: `9228`
- mode: `BACKGROUND`
- total rows reported: `190,013,447`
- reached: `98.42%`
- outcome: cancelled / not present

The job failed over near completion after `kotoba-compute-1` restarted. The
meta log reported `database 1 reset`; because the current license caps cluster
CPU below the live footprint, `DatabaseFailureIsolation` was unavailable and the
background job progress reset to `0.00%`. The index briefly appeared in catalog
while recovery completed, but the final post-cancel catalog check showed
`idx_vertex_legal_entity_lei` absent and `rw_ddl_progress` empty.

Retry only after one of these is true:

1. the license/core mismatch is resolved so background job failure isolation is
   effective; or
2. the cluster is temporarily reduced to a topology within the active license
   and has passed `rw-health-gate.sh`; or
3. a smaller LEI projection table is built and used instead of indexing the
   190M-row base table.

Until then, workers must keep `vertex_legal_entity` scans disabled and use
projection tables such as `vertex_contracts_organization` or
`vertex_open_lei_entity`.

### 2026-04-27 Resolver Population Step

Live counts showed both resolver projection tables were empty:

- `vertex_contracts_organization`: `0`
- `vertex_open_lei_entity`: `0`

The resolver now has a bounded exact-LEI fallback: if indexed projection lookup
misses and the request contains a 20-character LEI in `hints.lei` or `query`,
`intel.entity.resolve` calls the official GLEIF `/api/v1/lei-records/{lei}`
endpoint once, normalizes the record, idempotently inserts it into
`vertex_open_lei_entity`, and returns that projection candidate. This avoids
the failed 190M-row `vertex_legal_entity` index path while creating a real
resolver cache for subsequent indexed reads.

Keep this fallback limited to exact LEI lookups. Name search through GLEIF or
through local broad scans should remain an explicit opt-in path.

## Python External UDF Guidance

Python external UDFs are not a fix for unindexed resolver lookups. A UDF called
inside a predicate over `vertex_legal_entity` would still require scanning the
190M-row base table and would add a per-row language/RPC boundary. Keep the
resolver hot path on indexed equality predicates and projection tables.

Useful UDF shapes:

- normalize a small candidate set after indexed lookup;
- compute name similarity after `LIMIT` has already bounded rows;
- enrich resolver candidates with deterministic canonical keys during ingest;
- support offline/backfill jobs that write normalized projection columns.

Avoid:

- `WHERE python_udf(name) = ...` over large base tables;
- Python UDFs inside MV backfills over `vertex_legal_entity`;
- using UDFs as a substitute for `lei`, `did`, `source_record_id`, `src_vid`,
  or `dst_vid` indexes.

## MV Optimization Gaps

Heavy direct MV/view references observed:

- `mv_world_vertex_per_host` directly counts `vertex_legal_entity`,
  `vertex_spatial`, and `vertex_page`.
- `mv_legal_entity_by_country`, `mv_legal_entity_coverage`,
  `mv_legal_entity_disclosure_coverage`, `mv_entity_total`, and
  `mv_entity_with_did` directly reference `vertex_legal_entity`.
- `mv_maps_collected_per_source_label*` directly aggregate `vertex_spatial`.
- `mv_gov_record_dedup` groups over filtered `vertex_repo_record`.

Preferred follow-up:

1. Keep broad user-facing coverage queries on small rollup relations.
2. Add bounded intermediate MVs where cardinality is low, for example
   `mv_legal_entity_country_type_count` rather than wide legal-entity payload
   MVs.
3. Use plain `view_*` for runtime views and `mv_*` only for materialized views.
4. Move readers from `mv_world_coverage_live` to `view_world_coverage_live`,
   then drop or rematerialize the legacy name in a compatibility window.
