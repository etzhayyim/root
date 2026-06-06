---
id: adr-2605080500-sqlmesh-mv-management
title: "ADR-2605080500: SQLMesh MV Management — Replacing Kysely TypeScript for MV Definitions"
status: active
doc_type: adr
topic: sqlmesh-mv-management
authoritative: true
last_verified: 2026-05-07
priority: 7.0
axis: architecture
weight: 0.70
priority_note: "SQLMesh が MV SQL の正本 (source of truth)。Kysely MV migration を段階的に置き換え。RW streaming MV は DDL チャネル経由で適用"
authoritative_for:
  - SQLMesh project structure for Kotoba/Datomic MV definitions
  - MV SQL source of truth (sqlmesh/models/*.sql)
  - Migration path from Kysely TypeScript MV to SQLMesh
  - SQLMesh state schema (_sqlmesh) separation from vertex_*/edge_*/mv_*
depends_on:
  - adr-2605080300-sqlalchemy-core-usage-contract
  - adr-2605080000-distributed-cognitive-actor-system
related:
  - adr-2605080400-alembic-scope-contract
  - adr-2605080700-graph-schema-live-kotoba-baseline
amends: []
amended_by: []
supersedes: []
superseded_by: []
---

# ADR-2605080500: SQLMesh MV Management — Replacing Kysely TypeScript for MV Definitions

**Status**: accepted
**Date**: 2026-05-07
**Deciders**: Jun Kawasaki

## Context

Materialized view definitions today live as inline SQL strings inside Kysely
TypeScript migration files (`30-graph/graph-schema/migrations/`). This creates:

1. **No MV lineage** — there is no machine-readable dependency graph showing
   which MVs depend on which source tables or other MVs.
2. **Drift undetected** — if a source table schema changes, the dependent MV
   SQL is not automatically flagged as stale.
3. **No audit** — there is no way to diff the deployed MV SQL against the
   intended definition without manually querying `SHOW CREATE MATERIALIZED VIEW`.
4. **Refactoring friction** — renaming a column requires finding every MV
   that references it by grep.

SQLMesh models address all four by treating MV SQL as first-class Python/SQL
source files with a dependency graph.

## Decision

### Architecture: SQLMesh as SQL source of truth

```
sqlmesh/models/*.sql     ← SQL source of truth for each MV
        ↓ sqlmesh plan
Generated DDL diff       ← review (not auto-applied to RW)
        ↓ rw-health-gate.sh + psql
Kotoba/Datomic streaming MV  ← deployed MV (CREATE MATERIALIZED VIEW)
```

SQLMesh **does not** execute `CREATE MATERIALIZED VIEW` on Kotoba/Datomic directly.
Kotoba/Datomic streaming MVs use an incremental computation engine that differs from
standard PostgreSQL MVs — they cannot be wrapped in a `CREATE TABLE AS SELECT`.

Instead, SQLMesh:
1. Validates the SQL (parse + type-check against schema)
2. Computes lineage (dependency graph between models)
3. Generates the `CREATE MATERIALIZED VIEW … AS <SELECT>` DDL
4. Reports drift between deployed definition and model file

The generated DDL is applied through the existing RW DDL channel
(`rw-health-gate.sh` gate + psql).

### Rule 1: Each MV has a `sqlmesh/models/<mv_name>.sql` file

```sql
-- sqlmesh/models/mv_actor_social_stats.sql
MODEL (
  name dev.mv_actor_social_stats,
  kind FULL,
  dialect postgres,
  description 'Per-actor post + follow counts.',
  grain [actor_did],
  tags [social, actor, materialized_view]
);

SELECT
  normalize_actor_did(repo) AS actor_did,
  COUNT(*) FILTER (WHERE collection = 'app.bsky.feed.post') AS posts_count,
  MAX(ts_ms) AS last_activity_ms
FROM graphar.vertex_repo_record
GROUP BY 1
```

### Rule 2: MV kind = FULL (PostgreSQL-dialect; not RW streaming kind)

SQLMesh's `kind = FULL` maps to `CREATE OR REPLACE TABLE AS SELECT` in
execution, but here we use it as a **documentation contract** — the actual
Kotoba/Datomic DDL is `CREATE MATERIALIZED VIEW`. The dialect is `postgres` (closest
to Kotoba/Datomic's SQL).

### Rule 3: SQLMesh state lives in `_sqlmesh` schema

SQLMesh writes its internal state (model history, snapshots) to `_sqlmesh.*`
tables. This is separate from `vertex_*` / `edge_*` / `mv_*` (Kysely scope)
and `public.*` (Alembic scope).

### Rule 4: Kysely → SQLMesh migration path (incremental)

| Phase | Action |
|---|---|
| **Phase 0 (current)** | Existing Kysely `CREATE MATERIALIZED VIEW` migrations remain in `30-graph/graph-schema/migrations/`. SQLMesh models are added as the new canonical SQL source alongside. |
| **Phase 1** | New MVs are defined in `sqlmesh/models/` first. The Kysely migration references the SQLMesh model file via a `-- source: sqlmesh/models/<name>.sql` comment. |
| **Phase 2** | Existing MVs are back-ported to `sqlmesh/models/` one at a time. Kysely migrations retain the CREATE MATERIALIZED VIEW DDL but are flagged with `-- migrated-to-sqlmesh: true`. |
| **Phase 3** | All MV DDL originates from SQLMesh plan output. Kysely migrations contain only `DROP MATERIALIZED VIEW IF EXISTS … ; ` + reference to SQLMesh. |

No flag-day required — phases proceed incrementally.

### Rule 5: SQLMesh is a dev/tools dependency, lazy-loaded

SQLMesh (~60 MB) is in `[project.optional-dependencies] db-tools` and is never
imported in the hot-path PyZeebe worker code. Install only in tooling environments:

```
pip install "pymagatama[db-tools]"
```

---

## File Location

```
20-actors/magatama/py/
  sqlmesh/
    config.py          # Gateway config (RW + local DuckDB)
    models/
      mv_actor_social_stats.sql
      mv_canopy_shape.sql
      ...              # One .sql file per MV
    audits/            # SQLMesh audit definitions
    macros/            # Shared SQL macros (e.g. normalize_actor_did)
```

---

## Consequences

**Gained**:
- Machine-readable MV lineage (which MVs consume which tables)
- Schema drift detection (`sqlmesh audit`)
- Unified SQL source — editor syntax highlighting, lint, format
- Incremental migration path from Kysely without breaking existing deployments

**Constraints**:
- SQLMesh does not auto-apply streaming MVs to Kotoba/Datomic; DDL is applied manually
- Requires `rw-health-gate.sh` gate before any MV DDL change (existing constraint)
- Heavy dep (60 MB+); must not enter the worker image

---

## References

- `20-actors/magatama/py/sqlmesh/config.py`
- `20-actors/magatama/py/sqlmesh/models/`
- ADR-2605080300: SQLAlchemy Core Usage Contract
- ADR-2605080400: Alembic Scope Contract
- ADR-2605080700: graph-schema Live Kotoba/Datomic Baseline
- `30-graph/graph-schema/migrations/` (existing Kysely MV migrations)
- `50-infra/vultr/kotoba/scaling-contract.yaml` (DDL gate)
- `70-tools/scripts/ingest/rw-health-gate.sh`

---

## Addendum 2026-05-08 — Baseline Interaction

ADR-2605080700 changes the graph-schema baseline: new graph-schema DDL starts
from the live Kotoba/Datomic catalog, not from replaying Kysely migration history.
For MV work, SQLMesh remains the source for model SQL and lineage, while the
live Kotoba/Datomic catalog plus `src/database.ts` drift gate remains the deployed
schema truth.
