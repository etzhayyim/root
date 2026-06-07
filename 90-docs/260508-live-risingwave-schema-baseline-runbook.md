# Live Kotoba/Datomic Schema Baseline Runbook (2026-05-08)

ADR: `90-docs/adr/2605080700-graph-schema-live-kotoba-baseline.md`

## Current State

`30-graph/graph-schema` starts from the live Kotoba/Datomic catalog baseline:

- Active Alembic head: `live_kotoba_20260508`
- Active revision directory: `30-graph/graph-schema/alembic/current_versions/`
- Active version table: `graph_schema_alembic_live`
- Generated TypeScript schema: `30-graph/graph-schema/src/database.ts`
- Current generated size: 3332 tables / 52947 columns

Historical locations:

- Kysely archive: `30-graph/graph-schema/migrations/`
- Converted Alembic lineage: `30-graph/graph-schema/alembic/versions/`

These are lineage archives. Do not replay them into the live cluster.

## Pull Live Schema

```sh
cd 30-graph/graph-schema
DATABASE_URL=... pnpm db:gen
DATABASE_URL=... pnpm db:drift
```

Expected drift result:

```text
OK: no drift detected.
```

## Add New DDL

```sh
cd 30-graph/graph-schema
pnpm db:migrate:new -- "short description"
```

Place/edit active revisions under:

```text
alembic/current_versions/
```

Then apply, pull, and verify:

```sh
DATABASE_URL=... pnpm db:migrate
DATABASE_URL=... pnpm db:gen
DATABASE_URL=... pnpm db:drift
uv run alembic current
uv run alembic heads --verbose
```

## Add or Change MV SQL

Use SQLMesh model files for rebuildable MV SQL and lineage. Apply Kotoba/Datomic
streaming MV DDL through the existing gated DDL path; SQLMesh is not the direct
executor for Kotoba/Datomic streaming MVs.

## Hummock / Iceberg / Nessie

Current production path is Hummock-only. Iceberg/Nessie sink revisions remain
optional and must not be required for normal `db:gen`, `db:drift`, or baseline
operation.

## Failure Modes

- If `alembic current` reports an old Kysely-derived revision, verify that
  `alembic/env.py` is using `graph_schema_alembic_live`, not the historical
  version tables.
- If `db:drift` reports only `graph_schema_%` tables, keep them excluded from
  introspection; they are Alembic bookkeeping, not app schema.
- If generated table counts change while running the commands, rerun `db:gen`
  then `db:drift`; live Kotoba/Datomic DDL may have completed between reads.
