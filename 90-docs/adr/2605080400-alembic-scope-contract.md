---
id: adr-2605080400-alembic-scope-contract
title: "ADR-2605080400: Alembic Scope Contract — Python-Owned Tables Only"
status: active
doc_type: adr
topic: alembic-scope-contract
authoritative: true
last_verified: 2026-05-07
priority: 6.5
axis: architecture
weight: 0.65
priority_note: "Alembic は Python 所有テーブルのみ。vertex_*/edge_*/mv_* は Kysely TypeScript スコープ。RW トランザクション禁止"
authoritative_for:
  - Alembic usage scope (Python-owned tables only)
  - Alembic env.py for Kotoba/Datomic (no transaction wrapping)
  - Table name guard blocking vertex_* / edge_* / mv_* in Alembic migrations
depends_on:
  - adr-2605080300-sqlalchemy-core-usage-contract
related:
  - adr-2605080500-sqlmesh-mv-management
  - adr-2605080700-graph-schema-live-kotoba-baseline
amends: []
amended_by:
  - adr-2605080700-graph-schema-live-kotoba-baseline
supersedes: []
superseded_by: []
---

# ADR-2605080400: Alembic Scope Contract — Python-Owned Tables Only

**Status**: accepted
**Date**: 2026-05-07
**Deciders**: Jun Kawasaki

## Context

The graph-schema tables (`vertex_*`, `edge_*`, `mv_*`) are owned by the
Kysely TypeScript migration pipeline in `30-graph/graph-schema/migrations/`
(280+ migration files). Introducing Alembic without a hard scope boundary
risks dual ownership: the same table definition living in both a `.ts` file
and an Alembic revision, causing divergence and deployment conflicts.

Additionally, Kotoba/Datomic does not support DDL inside transactions (unlike
PostgreSQL). Standard Alembic wraps each migration in a transaction; this
must be disabled.

## Decision

### Rule 1: Alembic scope = Python-owned tables only

Alembic manages ONLY tables created to serve Python infrastructure:

| Table | Purpose |
|---|---|
| `pyzeebe_checkpoint` | LangGraph checkpointer state (if SqliteSaver → PostgresSaver) |
| `pyzeebe_migration` | Internal Alembic state (alembic_version) |
| `_sqlmesh.*` | SQLMesh state tables (if SQLMesh uses Alembic for its own state) |
| `py_audit_*` | Python-local audit tables that are NOT Kotoba/Datomic graph schema |

### Rule 2: Table name guard blocks forbidden prefixes

`alembic/env.py` scans each migration script for DDL statements that reference
tables starting with `vertex_`, `edge_`, `mv_`, or `graphar.`. Any such
reference raises a `RuntimeError` before the migration runs:

```
RuntimeError: Alembic migration 'xxx_add_foo.py' references table 'vertex_actor'
which starts with 'vertex_'. Graph-schema tables are owned by Kysely TypeScript
migrations in 30-graph/graph-schema/migrations/. Create the migration there.
```

### Rule 3: No transaction wrapping for Kotoba/Datomic DDL

`env.py` sets `transaction_per_migration=False` in both offline and online mode.
Kotoba/Datomic does not support `BEGIN` / `COMMIT` around CREATE TABLE / ALTER TABLE.

```python
# alembic/env.py
context.configure(
    connection=connection,
    target_metadata=target_metadata,
    transaction_per_migration=False,  # required for Kotoba/Datomic
    compare_type=True,
)
```

### Rule 4: Migration naming follows graph-schema convention

Migration files use the `%Y%m%d%H%M_<slug>` timestamp prefix (same as
Kysely migrations) to preserve chronological ordering:

```
alembic/versions/
  20260507120000_add_pyzeebe_checkpoint.py
  20260507130000_add_py_audit_table.py
```

---

## File Location

```
20-actors/magatama/py/
  alembic.ini
  alembic/
    env.py         # Kotoba/Datomic-compatible: no txn, table guard
    script.py.mako # Template with scope reminder
    versions/      # Timestamped migration files
```

---

## Consequences

**Gained**:
- Clear ownership boundary: Kysely owns graph schema, Alembic owns Python infra
- Runtime guard prevents accidental dual ownership
- Alembic autogenerate works safely against Python-only MetaData

**Constraints**:
- All `vertex_*`, `edge_*`, `mv_*` table changes go to
  `30-graph/graph-schema/migrations/` (TypeScript, not Python)
- Alembic `autogenerate` must use a MetaData that only reflects Python-owned
  tables (not `graphar.*`)

---

## References

- `20-actors/magatama/py/alembic/env.py`
- `20-actors/magatama/py/alembic.ini`
- ADR-2605080300: SQLAlchemy Core Usage Contract
- ADR-2605080500: SQLMesh MV Management
- ADR-2605080700: graph-schema Live Kotoba/Datomic Baseline
- `30-graph/graph-schema/migrations/` (Kysely TypeScript scope)

---

## Addendum 2026-05-08 — ML Serving Tables Exception (`vertex_lora_*`)

**Status**: active

### Context

The LoRA adapter lifecycle (train → register → serve → retire) is entirely
Python-driven: `runLora` BPMN task → pymagatama primitive → B2 upload →
`vertex_lora_adapter` row INSERT. The schema evolution of this table is
therefore most naturally co-located with the Python ML pipeline, not the
TypeScript graph-schema migrations.

Additionally, the P10v2 typed-column upgrade for `vertex_lora_adapter`
(adding `weight_b2_uri`, `weight_sha256`, `adapter_rank`, `adapter_alpha`,
`adapter_format`, `display_name_yomi`) is a Python-initiated schema change
required before any Python worker can write these columns.

### Amendment

**Rule 1 is extended**: Alembic may manage tables whose names match
`vertex_lora_*` in addition to the existing `pyzeebe_checkpoint`, `py_audit_*`,
and `_sqlmesh.*` scopes.

**Rationale for narrow exception** (not a blanket `vertex_*` allowance):
- `vertex_lora_*` tables are exclusively written by pymagatama Python workers
- No TypeScript CF Worker writes to `vertex_lora_adapter` directly
- The ML serving lifecycle (ONNX export / safetensors packaging / B2 upload)
  is a Python concern end-to-end
- Allowing all `vertex_*` in Alembic would re-introduce dual-ownership risk
  for the 280+ existing TypeScript-managed tables

### Guard update

`alembic/env.py` `_FORBIDDEN_TABLE_PREFIXES` is updated to exclude
`vertex_lora_` from the blocked set. The guard still blocks all other
`vertex_*`, `edge_*`, `mv_*` prefixes.

### Scope of exception

| Allowed in Alembic | Reason |
|---|---|
| `vertex_lora_adapter` | LoRA weight registry, Python-owned lifecycle |
| `vertex_lora_*` (future) | Future ML serving tables following same pattern |

| Still blocked in Alembic | Reason |
|---|---|
| `vertex_*` (non-lora) | Kysely TypeScript ownership |
| `edge_*` | Kysely TypeScript ownership |
| `mv_*` | SQLMesh ownership (ADR-2605080500) |

---

## Addendum 2026-05-08 — graph-schema Live Baseline

`30-graph/graph-schema` no longer uses the old Kysely TypeScript migration
chain as the active production migration graph. ADR-2605080700 establishes
`live_kotoba_20260508` as the baseline revision and moves active
graph-schema Alembic revisions to `30-graph/graph-schema/alembic/current_versions/`.

This does not relax the Python-worker Alembic scope in
`20-actors/magatama/py`. It only defines the graph-schema package's own
baseline and future DDL path.
