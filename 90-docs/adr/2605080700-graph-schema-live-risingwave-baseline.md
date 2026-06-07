---
id: adr-2605080700-graph-schema-live-kotoba-baseline
title: "ADR-2605080700: graph-schema Live Kotoba/Datomic Baseline"
status: active
doc_type: adr
topic: graph-schema-live-baseline
authoritative: true
last_verified: 2026-05-08
priority: 7.2
axis: architecture
weight: 0.72
priority_note: "graph-schema は live Kotoba/Datomic schema を baseline とし、過去 Kysely/Alembic 履歴を replay しない"
authoritative_for:
  - graph-schema live baseline policy
  - Active Alembic revision location for 30-graph/graph-schema
  - Kysely migration archive status
  - database.ts generation and drift gate
depends_on:
  - adr-2605080300-sqlalchemy-core-usage-contract
  - adr-2605080500-sqlmesh-mv-management
related:
  - adr-2605080400-alembic-scope-contract
supersedes: []
superseded_by: []
---

# ADR-2605080700: graph-schema Live Kotoba/Datomic Baseline

**Status**: accepted
**Date**: 2026-05-08
**Deciders**: Jun Kawasaki

## Context

`30-graph/graph-schema/migrations/` contains the historical Kysely migration
archive. That archive has been converted to Alembic lineage files, but replaying
the full chain into the current production Kotoba/Datomic cluster is the wrong
operational model:

- The live cluster already includes out-of-band schema changes that were applied
  directly through Kotoba/Datomic DDL channels.
- Kotoba/Datomic has PostgreSQL-wire compatibility gaps that make generic Alembic
  replay brittle (`VARCHAR(n)`, version table PK/update behavior, and DDL
  visibility/flush semantics).
- Nessie and Iceberg sinks are not in current use; the production data plane is
  Hummock only.
- `src/database.ts` is already generated from live `information_schema`, making
  the running DB the best baseline artifact.

## Decision

Start `30-graph/graph-schema` schema management from the current live
Kotoba/Datomic schema rather than replaying historical Kysely migrations.

The active Alembic graph is:

```text
30-graph/graph-schema/alembic/current_versions/
  20260508_live_kotoba_baseline.py  # revision live_kotoba_20260508
```

Historical converted revisions remain under:

```text
30-graph/graph-schema/alembic/versions/
```

They are retained for lineage and audit, not for production replay.

## Operating Rules

1. Pull live schema before committing graph-schema changes:

```sh
cd 30-graph/graph-schema
DATABASE_URL=... pnpm db:gen
DATABASE_URL=... pnpm db:drift
```

2. New graph-schema DDL goes into `alembic/current_versions/` from the
   `live_kotoba_20260508` baseline.

3. Rebuildable MV SQL goes into SQLMesh model files first. Kotoba/Datomic streaming
   MV DDL is applied through the existing gated DDL channel, not direct SQLMesh
   execution.

4. Legacy Kysely migrations in `migrations/` are immutable historical input.
   Do not add new TypeScript migrations for graph-schema DDL.

5. Iceberg/Nessie paths remain optional. The default production path is
   Hummock-only.

## Verification Snapshot

Verified on 2026-05-08:

- `uv run alembic current` -> `live_kotoba_20260508 (head)`
- `uv run alembic heads --verbose` -> single active head
- `uv run python -m graph_schema.generate_database_ts` -> 3332 tables / 52947 columns
- `uv run python -m graph_schema.drift` -> no drift
- `uv run python -m compileall graph_schema alembic` -> OK

## Consequences

**Gained**:

- No flag-day replay of 1265 legacy Kysely migrations.
- The repo baseline matches the actual production Kotoba/Datomic catalog.
- Future DDL has a clean Alembic start point.
- `database.ts` remains an exact generated reflection of live schema.

**Constraints**:

- Historical Alembic lineage under `alembic/versions/` is not the active
  migration graph.
- `alembic current` is authoritative only for the `graph_schema_alembic_live`
  version table.
- Every schema change must regenerate and drift-check `src/database.ts`.

## References

- `30-graph/graph-schema/alembic/current_versions/20260508_live_kotoba_baseline.py`
- `30-graph/graph-schema/alembic.ini`
- `30-graph/graph-schema/alembic/env.py`
- `30-graph/graph-schema/graph_schema/generate_database_ts.py`
- `30-graph/graph-schema/graph_schema/drift.py`
- `30-graph/deps.toml`
