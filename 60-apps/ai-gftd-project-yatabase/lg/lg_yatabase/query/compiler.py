"""Compile a PatternSpec into RisingWave MV + index DDL.

Constraints:
- No ON CONFLICT, no UNIQUE, no WITH RECURSIVE (RW streaming mode)
- graphar schema: vertex tables = graphar.vertex_{label}, edge tables = graphar.edge_{label}
- Edge direction 'out': src_id joins from left vertex, dst_id joins to right vertex
- Edge direction 'in': dst_id joins from left vertex, src_id joins to right vertex
- Edge direction 'both': uses a UNION of out + in (generates two separate MVs joined via UNION ALL)
"""
from __future__ import annotations

import hashlib
import re

from lg_yatabase.query.models import EdgeStep, PatternSpec, VertexStep

_SAFE_LABEL = re.compile(r"^[a-z][a-z0-9_]{0,62}$")
_SAFE_ALIAS = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
_SAFE_FIELD = re.compile(r"^[a-z][a-z0-9_]{0,62}$")


def _safe(val: str, pattern: re.Pattern, name: str) -> str:
    if not pattern.match(val):
        raise ValueError(f"invalid {name}: {val!r}")
    return val


def _org_hash8(org_did: str) -> str:
    return hashlib.sha256(org_did.encode()).hexdigest()[:8]


def _query_hash8(steps_json: str, select_json: str | None) -> str:
    payload = steps_json + (select_json or "")
    return hashlib.sha256(payload.encode()).hexdigest()[:8]


def mv_name(org_did: str, steps_json: str, select_json: str | None) -> str:
    return f"graphar.mv_yata_{_org_hash8(org_did)}_{_query_hash8(steps_json, select_json)}"


def compile_ddl(spec: PatternSpec, mv: str, static_where: dict | None = None) -> str:
    """Return full DDL string: CREATE MV + CREATE INDEX statements."""
    vertex_steps: list[tuple[int, VertexStep]] = [
        (i, s) for i, s in enumerate(spec.steps) if isinstance(s, VertexStep)
    ]
    edge_steps: list[tuple[int, EdgeStep]] = [
        (i, s) for i, s in enumerate(spec.steps) if isinstance(s, EdgeStep)
    ]

    # Validate labels and aliases
    for _, vs in vertex_steps:
        _safe(vs.label, _SAFE_LABEL, "vertex label")
        _safe(vs.alias, _SAFE_ALIAS, "vertex alias")
    for _, es in edge_steps:
        _safe(es.label, _SAFE_LABEL, "edge label")

    # Build SELECT clause
    select_cols: list[str] = []
    for col_ref in spec.select:
        parts = col_ref.split(".", 1)
        if len(parts) != 2:
            raise ValueError(f"select item must be 'alias.field': {col_ref!r}")
        alias, field = parts
        _safe(alias, _SAFE_ALIAS, "select alias")
        _safe(field, _SAFE_FIELD, "select field")
        select_cols.append(f"{alias}.{field} AS {alias}_{field}")

    # Default SELECT: all vertex.vertex_id + vertex.name
    if not select_cols:
        for _, vs in vertex_steps:
            select_cols.append(f"{vs.alias}.vertex_id AS {vs.alias}_vertex_id")
            select_cols.append(f"{vs.alias}.name AS {vs.alias}_name")

    select_clause = ",\n  ".join(select_cols)

    # Build FROM + JOIN chain
    first_alias = vertex_steps[0][1].alias
    first_label = vertex_steps[0][1].label
    from_clause = f"graphar.vertex_{first_label} {first_alias}"

    join_parts: list[str] = []
    for hop_idx, (_, es) in enumerate(edge_steps):
        left_vs = vertex_steps[hop_idx][1]
        right_vs = vertex_steps[hop_idx + 1][1]
        e_alias = f"_e{hop_idx}"

        if es.direction == "out":
            join_parts.append(
                f"JOIN graphar.edge_{es.label} {e_alias}"
                f" ON {left_vs.alias}.vertex_id = {e_alias}.src_id"
            )
            join_parts.append(
                f"JOIN graphar.vertex_{right_vs.label} {right_vs.alias}"
                f" ON {e_alias}.dst_id = {right_vs.alias}.vertex_id"
            )
        elif es.direction == "in":
            join_parts.append(
                f"JOIN graphar.edge_{es.label} {e_alias}"
                f" ON {left_vs.alias}.vertex_id = {e_alias}.dst_id"
            )
            join_parts.append(
                f"JOIN graphar.vertex_{right_vs.label} {right_vs.alias}"
                f" ON {e_alias}.src_id = {right_vs.alias}.vertex_id"
            )
        else:  # both
            join_parts.append(
                f"JOIN graphar.edge_{es.label} {e_alias}"
                f" ON {left_vs.alias}.vertex_id = {e_alias}.src_id"
                f" OR {left_vs.alias}.vertex_id = {e_alias}.dst_id"
            )
            join_parts.append(
                f"JOIN graphar.vertex_{right_vs.label} {right_vs.alias}"
                f" ON CASE WHEN {left_vs.alias}.vertex_id = {e_alias}.src_id"
                f" THEN {e_alias}.dst_id ELSE {e_alias}.src_id END = {right_vs.alias}.vertex_id"
            )

    join_clause = "\n".join(join_parts)

    # Optional static WHERE
    where_clause = ""
    if static_where:
        field_ref = static_where.get("field", "")
        op = static_where.get("op", "eq")
        value = static_where.get("value", "")
        parts = field_ref.split(".", 1)
        if len(parts) != 2:
            raise ValueError(f"staticWhere.field must be 'alias.field': {field_ref!r}")
        alias_w, field_w = parts
        _safe(alias_w, _SAFE_ALIAS, "where alias")
        _safe(field_w, _SAFE_FIELD, "where field")
        sql_op = {"eq": "=", "neq": "!=", "gt": ">", "lt": "<", "gte": ">=", "lte": "<="}.get(op, "=")
        # Escape value — only allow safe string/numeric values
        if isinstance(value, (int, float)):
            val_sql = str(value)
        else:
            val_sql = "'" + str(value).replace("'", "''") + "'"
        where_clause = f"\nWHERE {alias_w}.{field_w} {sql_op} {val_sql}"

    mv_sql = (
        f"CREATE MATERIALIZED VIEW {mv} AS\nSELECT\n  {select_clause}\n"
        f"FROM {from_clause}\n{join_clause}{where_clause};"
    )

    # Build index DDL
    index_sqls: list[str] = []
    for col_ref in spec.index_on:
        parts = col_ref.split(".", 1)
        if len(parts) != 2:
            raise ValueError(f"indexOn item must be 'alias.field': {col_ref!r}")
        alias_i, field_i = parts
        col_name = f"{alias_i}_{field_i}"
        idx_name = f"idx_{mv.split('.')[-1]}_{col_name}"
        index_sqls.append(f"CREATE INDEX {idx_name} ON {mv} ({col_name});")

    # Default index on first vertex.vertex_id
    if not index_sqls:
        first_col = f"{first_alias}_vertex_id"
        idx_name = f"idx_{mv.split('.')[-1]}_{first_col}"
        index_sqls.append(f"CREATE INDEX {idx_name} ON {mv} ({first_col});")

    parts_ddl = [mv_sql] + index_sqls
    return "\n\n".join(parts_ddl)
