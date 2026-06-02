"""Generic-primitive worker for com.etzhayyim.tools.sql.* (ADR-2605082000 §2 follow-up).

Provides a read-only SELECT primitive that LangGraph nodes can bind to
without per-actor py_primitive code. Strict guard: rejects anything that
isn't a SELECT / WITH-CTE-SELECT.

Wired into mcp_dispatch via ``register_overrides``.
"""

from __future__ import annotations

import re
from typing import Any

# Allow only these leading keywords (case-insensitive, after whitespace +
# optional /* ... */ leading comment).
_READONLY_RE = re.compile(
    r"\A\s*(?:/\*[\s\S]*?\*/\s*)?(SELECT|WITH)\b",
    re.IGNORECASE,
)
_DEFAULT_LIMIT = 1000


def _is_readonly(sql: str) -> bool:
    if not isinstance(sql, str) or not sql.strip():
        return False
    return bool(_READONLY_RE.match(sql))


def _row_to_dict(row: Any) -> dict[str, Any]:
    # SQLAlchemy 2.x rows expose ._mapping. Tuples fall back to numeric keys.
    mapping = getattr(row, "_mapping", None)
    if mapping is not None:
        return {k: v for k, v in dict(mapping).items()}
    if isinstance(row, dict):
        return dict(row)
    if isinstance(row, (list, tuple)):
        return {f"c{i}": v for i, v in enumerate(row)}
    return {"value": row}


_RESERVED_KWARGS = {"sql", "params", "limit", "rows", "confirmWrite"}

# Strict allow-list for ``task_sql_exec``: only INSERT / UPDATE / UPSERT
# (incl. WITH … INSERT … RETURNING). DELETE / DROP / TRUNCATE / GRANT /
# CREATE / ALTER are rejected.
_WRITE_ALLOW_RE = re.compile(
    r"\A\s*(?:/\*[\s\S]*?\*/\s*)?(INSERT|UPDATE|UPSERT|WITH)\b",
    re.IGNORECASE,
)
_WRITE_DENY_RE = re.compile(
    r"\b(DELETE|DROP|TRUNCATE|GRANT|REVOKE|CREATE|ALTER)\b",
    re.IGNORECASE,
)


async def task_sql_query(
    *,
    sql: str = "",
    params: dict[str, Any] | None = None,
    limit: int | None = None,
    **extra_kwargs: Any,
) -> dict[str, Any]:
    """Run a read-only SELECT and return the rows as objects.

    Bind params come from two sources, merged in order:
      1. ``params`` dict (config.args.params or explicit kwarg)
      2. ``extra_kwargs`` — any kwarg other than ``sql`` / ``params`` /
         ``limit`` is treated as a named bind. This is the LangGraph
         input_keys path: ``input_keys=["industry_codes"]`` makes
         ``state["industry_codes"]`` available as ``%(industry_codes)s``
         in the SQL without per-call params dict construction.
      Explicit ``params`` entries win over kwarg-derived ones on conflict.

    Returns ``{"error": ...}`` on rejection / failure. ``limit`` (default
    1000) caps the response payload size to protect callers / hosts.
    """
    if not _is_readonly(sql):
        return {"error": "com.etzhayyim.tools.sql.query: SQL must start with SELECT or WITH"}
    cap = int(limit) if limit is not None else _DEFAULT_LIMIT
    merged_params: dict[str, Any] = {
        k: v for k, v in extra_kwargs.items() if k not in _RESERVED_KWARGS
    }
    if params:
        merged_params.update(params)
    try:
        from pymagatama.db_alchemy import sa_query
    except Exception as exc:
        return {"error": f"db_alchemy unavailable: {exc}"}
    try:
        raw = sa_query(sql, merged_params)
    except Exception as exc:  # pragma: no cover — defensive
        return {"error": f"sql_query failed: {exc}"}
    rows = [_row_to_dict(r) for r in (raw or [])]
    if cap > 0 and len(rows) > cap:
        rows = rows[:cap]
    return {"rows": rows, "rowCount": len(rows)}


def _is_writeable(sql: str) -> tuple[bool, str | None]:
    if not isinstance(sql, str) or not sql.strip():
        return (False, "SQL is required")
    if not _WRITE_ALLOW_RE.match(sql):
        return (False, "SQL must start with INSERT / UPDATE / UPSERT / WITH")
    if _WRITE_DENY_RE.search(sql):
        return (False, "SQL contains forbidden keyword (DELETE / DROP / TRUNCATE / GRANT / REVOKE / CREATE / ALTER)")
    return (True, None)


async def task_sql_exec(
    *,
    sql: str = "",
    params: dict[str, Any] | None = None,
    rows: list[dict[str, Any]] | None = None,
    confirmWrite: bool = False,
    **extra_kwargs: Any,
) -> dict[str, Any]:
    """Run a write SQL (INSERT / UPDATE / UPSERT) and return the rowcount.

    Strict guards:
      - ``confirmWrite`` must be True (defense-in-depth).
      - SQL must start with INSERT / UPDATE / UPSERT / WITH.
      - SQL must NOT contain DELETE / DROP / TRUNCATE / GRANT / REVOKE /
        CREATE / ALTER (case-insensitive substring check).

    Modes:
      - If ``rows`` is supplied → ``sa_executemany`` batch mode.
        Returns ``{"rowCount": <total processed>}``.
      - Else → single ``sa_rowcount`` execute. Returns affected count.
    """
    if not confirmWrite:
        return {"error": "com.etzhayyim.tools.sql.exec: confirmWrite must be true"}
    ok, why = _is_writeable(sql)
    if not ok:
        return {"error": f"com.etzhayyim.tools.sql.exec: {why}"}

    merged_params: dict[str, Any] = {
        k: v for k, v in extra_kwargs.items() if k not in _RESERVED_KWARGS
    }
    if params:
        merged_params.update(params)

    try:
        from sqlalchemy import text as sa_text
        from pymagatama.db_alchemy import sa_executemany, sa_rowcount
    except Exception as exc:
        return {"error": f"db_alchemy unavailable: {exc}"}

    try:
        clause = sa_text(sql)
        if rows is not None:
            if not isinstance(rows, list):
                return {"error": "rows must be a list of objects"}
            count = sa_executemany(clause, rows)
        else:
            count = sa_rowcount(clause, merged_params)
    except Exception as exc:  # pragma: no cover — defensive
        return {"error": f"sql_exec failed: {exc}"}

    return {"rowCount": int(count or 0)}


# ---------------------------------------------------------------------------
# task_sql_insert_row  (ADR-2605082000 Phase E0 — dynamic-column INSERT)
# ---------------------------------------------------------------------------


# Allow only safe identifier shape for `table` (defense-in-depth — even
# though we never interpolate untrusted input directly into SQL, build
# via SQLAlchemy Table reflection-style construction).
_TABLE_NAME_RE = re.compile(r"\A[a-zA-Z_][a-zA-Z0-9_]{0,127}\Z")
_COLUMN_NAME_RE = re.compile(r"\A[a-zA-Z_][a-zA-Z0-9_]{0,127}\Z")


def _render_vertex_id(template: str, owner_did: str, collection: str) -> str:
    """Expand a vertex_id template per the ADR-2605082000 Phase E convention.

    Placeholders:
      {owner_did}  — caller-provided DID, e.g. did:web:bpmn.etzhayyim.com
      {collection} — caller-provided NSID,  e.g. com.etzhayyim.apps.hr.event
      {stamp}      — UTC YYYYMMDDHHMMSS
      {nanoid8}    — 8-char hex nanoid (uuid4 first 8)

    Unknown placeholders pass through unchanged so the caller sees the
    literal `{foo}` if they typoed.
    """
    import datetime as _dt
    import uuid as _uuid
    stamp = _dt.datetime.now(tz=_dt.UTC).strftime("%Y%m%d%H%M%S")
    nanoid8 = _uuid.uuid4().hex[:8]
    return (template
            .replace("{owner_did}", owner_did or "")
            .replace("{collection}", collection or "")
            .replace("{stamp}", stamp)
            .replace("{nanoid8}", nanoid8))


async def task_sql_insert_row(
    *,
    table: str = "",
    row: dict[str, Any] | None = None,
    vertex_id_template: str | None = None,
    owner_did: str = "",
    collection: str = "",
    **_ignored: Any,
) -> dict[str, Any]:
    """Insert a row with runtime-determined columns into ``table``.

    Bridges the ADR-2605082000 Phase E LLM-supervisor decomposition pattern:
    LLM returns ``db_writes: [{"table": "...", "row": {...}}, ...]``, foreach
    iterates, each iteration calls this primitive with one ``{table, row}``
    item. The set of columns is data-driven (LLM picks them) so a fixed
    SQL template (sql.exec) doesn't fit.

    Auto-derive ``vertex_id`` if absent and ``vertex_id_template`` is given.
    Returns ``{"vertexId": <str>, "ok": true}`` or ``{"error": ...}``.

    Safety:
      - ``table`` must match ``^[a-zA-Z_][a-zA-Z0-9_]*$`` (rejects schema
        prefixes / DDL injection / quoted names).
      - Each column key in ``row`` must match the same identifier shape.
      - Values are passed through SQLAlchemy parameter binding — never
        string-interpolated into SQL.
      - No ``DELETE`` / ``UPDATE`` semantics here; only INSERT.
    """
    if not table or not _TABLE_NAME_RE.match(table):
        return {"error": "com.etzhayyim.tools.sql.insert_row: invalid table name"}
    if not isinstance(row, dict) or not row:
        return {"error": "com.etzhayyim.tools.sql.insert_row: 'row' must be a non-empty object"}
    bad_cols = [k for k in row if not _COLUMN_NAME_RE.match(str(k))]
    if bad_cols:
        return {"error": f"com.etzhayyim.tools.sql.insert_row: invalid column names: {bad_cols}"}

    # Derive vertex_id if missing and template given.
    work = dict(row)
    if not work.get("vertex_id") and vertex_id_template:
        work["vertex_id"] = _render_vertex_id(vertex_id_template, owner_did, collection)

    try:
        from sqlalchemy import Table, Column, String, MetaData
        from pymagatama.db_alchemy import sa_metadata, sa_rowcount
    except Exception as exc:
        return {"error": f"db_alchemy unavailable: {exc}"}

    try:
        cols = [Column(k, String) for k in work]
        # extend_existing=True so multiple iterations of foreach against the
        # same table reuse the SQLAlchemy Table object instead of erroring.
        t = Table(table, sa_metadata(), *cols, extend_existing=True)
        # Coerce all values to str — RisingWave column types vary per actor
        # but accept string coercion at INSERT (matches etzhayyim_company_ops
        # `_db_insert` pattern this primitive replaces).
        bound = {k: (str(v) if v is not None else None) for k, v in work.items()}
        sa_rowcount(t.insert(), bound)
    except Exception as exc:  # pragma: no cover — defensive
        return {"error": f"sql_insert_row failed: {exc}"}

    return {"vertexId": work.get("vertex_id", ""), "ok": True}
