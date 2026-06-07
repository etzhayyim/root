---
id: adr-2605080300-sqlalchemy-core-usage-contract
title: "ADR-2605080300: SQLAlchemy Core Usage Contract"
status: active
doc_type: adr
topic: sqlalchemy-core-usage-contract
authoritative: true
last_verified: 2026-05-07
priority: 7.0
axis: architecture
weight: 0.70
priority_note: "L6 クエリビルダー契約。SA Core のみ。ORM/Session/autoflush 禁止。GuardedCursor を保持"
authoritative_for:
  - SQLAlchemy usage at L6 compute boundaries
  - sa_execute() / sa_query() / sa_rowcount() L6 hot-path helpers
  - get_sa_engine() for Alembic / offline DDL only
  - No SA ORM / Session / autoflush / relationship
depends_on:
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605080200-pydantic-l6-validation-contract
related:
  - adr-2605080400-alembic-scope-contract
  - adr-2605080500-sqlmesh-mv-management
amends: []
amended_by: []
supersedes: []
superseded_by: []
---

# ADR-2605080300: SQLAlchemy Core Usage Contract

**Status**: accepted
**Date**: 2026-05-07
**Deciders**: Jun Kawasaki

## Context

L6 PyZeebe handlers use `db_sync.py` (`sync_cursor()` + `GuardedCursor`) for
all Kotoba/Datomic access. Ad-hoc SQL string concatenation in handler code creates
two problems:

1. **No type safety** — column references are plain strings; schema drift is
   silent until runtime.
2. **No composition** — complex WHERE clauses with variable filter predicates
   require error-prone string building.

SQLAlchemy Core's expression language solves both without introducing ORM
overhead (Session / identity map / autoflush / relationship). The existing
`db_sync.py` pool and `GuardedCursor` DDL guard must be preserved.

## Decision

### Rule 1: SQLAlchemy Core only — no ORM

```python
# ALLOWED: expression language
from sqlalchemy import select, insert, text, Table, Column, String
from pymagatama.db_alchemy import sa_execute, sa_metadata

t = Table("vertex_actor", sa_metadata(), Column("actor_did", String))
rows = sa_execute(select(t).where(t.c.actor_did == did))

# ALLOWED: raw text() for complex RW-specific SQL
rows = sa_execute(
    text("SELECT actor_did FROM mv_actor_social_stats WHERE posts_count > %(n)s"),
    {"n": 100},
)

# FORBIDDEN: ORM mapper / Session / relationship
# from sqlalchemy.orm import Session, DeclarativeBase  ← forbidden
```

### Rule 2: `sa_execute()` / `sa_query()` for hot-path L6 handlers

`sa_execute(clause, params=None)` compiles the SQLAlchemy expression to a
`%(name)s`-parameterised SQL string using the PostgreSQL dialect, then executes
via `sync_cursor()` from `db_sync.py`.

This means:
- `GuardedCursor` DDL guard remains active
- `prepare_threshold=0` (set on pool in `db_sync.py`) prevents RW prepared-
  statement rejection
- No parallel connection pool is created

```python
from pymagatama.db_alchemy import sa_execute, sa_rowcount
from sqlalchemy import text

# Query
rows = sa_execute(
    text("SELECT * FROM vertex_growth_event WHERE actor_did = %(did)s LIMIT 10"),
    {"did": actor_did},
)

# DML
n = sa_rowcount(
    text("UPDATE vertex_prune_intent SET status = 'applied' WHERE intent_id = %(id)s"),
    {"id": intent_id},
)
```

### Rule 3: `get_sa_engine()` is for Alembic / offline DDL only

`get_sa_engine()` creates a `NullPool` SQLAlchemy engine backed directly by
`KOTOBA_URL`. It attaches a `before_cursor_execute` event that calls
`_validate_sql_guard()` from `db_sync.py`, replicating the GuardedCursor
behaviour.

**Do not** call `get_sa_engine()` inside PyZeebe task handlers — use
`sa_execute()` / `sa_query()` instead.

```python
# alembic/env.py (ONLY usage of get_sa_engine)
from pymagatama.db_alchemy import get_sa_engine
engine = get_sa_engine()
```

### Rule 4: `sa_executemany()` for batch INSERT

Use `sa_executemany(stmt, rows_list, chunk_size=500)` for bulk INSERT operations.
It chunks the rows and uses `cursor.executemany()`, consistent with the
`psycopg cur.executemany(sql, batch)` pattern already used in shosha/adsk
primitives.

---

## File Location

```
20-actors/magatama/py/src/pymagatama/db_alchemy.py
```

Exports:
- `get_sa_engine()` — Alembic / offline only
- `sa_metadata()` — shared MetaData instance
- `sa_execute(clause, params)` — L6 hot-path
- `sa_execute_one(clause, params)` — first row or None
- `sa_query(clause, params)` — alias for sa_execute
- `sa_rowcount(clause, params)` — DML rowcount
- `sa_executemany(clause, rows, chunk_size)` — bulk INSERT

---

## Consequences

**Gained**:
- Type-safe column references via `Table` / `Column` declarations
- Dialect-aware compilation — same expression works on RW and test DuckDB
- Complex WHERE composition without string concatenation
- `sa_executemany` batch INSERT consistent with existing shosha/adsk patterns

**Constraints**:
- No SA ORM. `DeclarativeBase`, `Session`, `relationship` are forbidden.
- `get_sa_engine()` must not appear in hot-path worker code.
- `Table` declarations in L6 handlers are lightweight (no DB round-trip) and
  are safe to define inline.

---

## References

- `20-actors/magatama/py/src/pymagatama/db_sync.py` (GuardedCursor, sync pool)
- ADR-2605080200: Pydantic v2 L6 Validation Contract
- ADR-2605080400: Alembic Scope Contract
