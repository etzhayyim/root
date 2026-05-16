from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.engine import Engine


@dataclass(frozen=True)
class Column:
    table_name: str
    table_type: str
    column_name: str
    data_type: str
    is_nullable: str
    ordinal_position: int


def load_columns(engine: Engine) -> list[Column]:
    query = text(
        """
        SELECT
          c.table_name,
          t.table_type,
          c.column_name,
          c.data_type,
          c.is_nullable,
          c.ordinal_position
        FROM information_schema.columns c
        JOIN information_schema.tables t
          ON t.table_schema = c.table_schema AND t.table_name = c.table_name
        WHERE c.table_schema = 'public'
          AND t.table_type IN ('BASE TABLE', 'VIEW', 'MATERIALIZED VIEW')
          AND c.table_name NOT LIKE 'kysely_migration%'
          AND c.table_name NOT LIKE 'graph_schema_%'
          AND c.table_name NOT LIKE 'rw_%'
        ORDER BY c.table_name, c.ordinal_position
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query).mappings().all()
    return [
        Column(
            table_name=str(row["table_name"]),
            table_type=str(row["table_type"]),
            column_name=str(row["column_name"]),
            data_type=str(row["data_type"]),
            is_nullable=str(row["is_nullable"]),
            ordinal_position=int(row["ordinal_position"]),
        )
        for row in rows
    ]


def pascal(value: str) -> str:
    return "".join(part[:1].upper() + part[1:] for part in value.replace("-", "_").split("_") if part)


def row_type_name(table: str) -> str:
    return f"{pascal(table)}Row"


def map_type(data_type: str) -> str:
    t = data_type.lower()
    if "varchar" in t or t in {"text", "character", "char"} or t.startswith("character varying"):
        return "string"
    if t in {"bigint", "int8"}:
        return "number | bigint"
    if t in {"integer", "int", "int4", "smallint", "int2"}:
        return "number"
    if (
        "double precision" in t
        or t in {"real", "float4", "float8"}
        or t.startswith("numeric")
        or t.startswith("decimal")
    ):
        return "number"
    if t in {"boolean", "bool"}:
        return "boolean"
    if t == "date" or t.startswith("timestamp"):
        return "Date | string"
    if t in {"json", "jsonb"} or t.startswith("struct"):
        return "unknown"
    if t == "bytea":
        return "Uint8Array"
    return "string"


def ts_key(identifier: str) -> str:
    if identifier.replace("_", "").isalnum() and (identifier[0].isalpha() or identifier[0] == "_"):
        return identifier
    return repr(identifier)
