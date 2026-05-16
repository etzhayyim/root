from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from graph_schema.db import make_engine
from graph_schema.introspection import Column, load_columns, map_type, row_type_name, ts_key


OUT_PATH = Path(__file__).resolve().parents[1] / "src" / "database.ts"


def render(cols: list[Column]) -> str:
    by_table: dict[str, list[Column]] = defaultdict(list)
    for col in cols:
        by_table[col.table_name].append(col)

    lines: list[str] = [
        "/* eslint-disable */",
        "/**",
        " * Kysely-compatible database types for the GFTD graph DB (RisingWave).",
        " *",
        " * GENERATED FILE - do not edit by hand.",
        " * Regenerate with: DATABASE_URL=... pnpm db:gen",
        " * Verify with:    DATABASE_URL=... pnpm db:drift",
        " *",
        " * Source: live RisingWave `information_schema.columns` via SQLAlchemy.",
        " * Schema SSoT is the DB itself; Alembic migrations and SQLMesh models are",
        " * the durable source of schema change. See `CLAUDE.md`.",
        " */",
        "",
        "import type { ColumnType } from 'kysely';",
        "",
        "// Silence unused-import warning when no generated column uses ColumnType.",
        "type _KeepColumnType = ColumnType<never, never, never>;",
        "",
        "// --- Row interfaces (one per table / view / MV) ---",
        "",
    ]

    for table in sorted(by_table):
        lines.append(f"export interface {row_type_name(table)} {{")
        for col in by_table[table]:
            lines.append(f"  {ts_key(col.column_name)}?: {map_type(col.data_type)} | null;")
        lines.append("}")
        lines.append("")

    lines.append("// --- Database interface (table name -> Row type) ---")
    lines.append("")
    lines.append("export interface Database {")
    for table in sorted(by_table):
        lines.append(f"  {ts_key(table)}: {row_type_name(table)};")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    engine = make_engine()
    cols = load_columns(engine)
    OUT_PATH.write_text(render(cols), encoding="utf-8")
    tables = {col.table_name for col in cols}
    print(f"wrote {OUT_PATH}: {len(tables)} tables, {len(cols)} columns")


if __name__ == "__main__":
    main()
