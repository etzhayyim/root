# 30-graph DSM (Query Stack)

SSOT:
- Live RisingWave schema — durable deployed schema baseline (`live_risingwave_20260508`).
- `30-graph/graph-schema/src/database.ts` — generated TS reflection of live RisingWave `information_schema`.
- `30-graph/graph-schema/alembic/current_versions/` — active Alembic revisions for future DDL.
- `30-graph/deps.toml` — per-component metadata and vertex DID tier policy.
- `/deps.toml` — root index, layer rules (`[app_layer.*]`), enforcement input for `etzhayyim deps graph`.

## Layer Order

1. `graph-schema` (TS DB types generated from live RisingWave `information_schema`, with SQLAlchemy/Alembic/SQLMesh schema tooling)
2. `graph-planner`, `query-codegen`, `query-pushdown`, `vectorization`
3. `query-executor`
4. `query-coordinator`
5. `kagami` compat facade / integration package

Rule: upper layer depends only on lower layers.

## Component Roles

- `graph-schema`: Kysely-compatible `Database` + Row interfaces in `src/database.ts`; active schema management starts from the live RisingWave baseline in `alembic/current_versions`; derived models use SQLMesh; regenerate with `DATABASE_URL=... pnpm db:gen`; verify with `DATABASE_URL=... pnpm db:drift`.
- `graph-planner`: Cypher parse/plan/transpile + `validatePlanEfficiency()`
- `query-codegen`: SQL emission strategy interface
- `query-pushdown`: predicate/projection/limit pushdown strategy
- `vectorization`: embedding/vector workflow interface
- `query-executor`: executes planned steps on adapters
- `query-coordinator`: orchestrates planner/pushdown/executor/vectorization

## Dependency Matrix (DSM)

`1` means row depends on column.

| component \\ depends on | graph-schema | graph-planner | query-codegen | query-pushdown | vectorization | query-executor | query-coordinator |
|---|---:|---:|---:|---:|---:|---:|---:|
| graph-schema | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| graph-planner | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| query-codegen | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| query-pushdown | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| vectorization | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| query-executor | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| query-coordinator | 0 | 1 | 0 | 0 | 1 | 1 | 0 |

## Notes

- Keep `graph-planner` pure (no storage/network code).
- Keep `query-executor` storage-adapter facing (read/write providers).
- Keep `query-coordinator` orchestration-only (no direct schema mutation).
- Schema changes: write active Alembic migration under `graph-schema/alembic/current_versions/` or SQLMesh model → apply to RisingWave → `DATABASE_URL=... pnpm db:gen` → `DATABASE_URL=... pnpm db:drift` → commit migration/model and regenerated `src/database.ts`.
- Historical `graph-schema/migrations/` and `graph-schema/alembic/versions/` are lineage archives after ADR-2605080700; do not replay them into the live cluster.
