from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from graph_schema.db import make_engine
from graph_schema.introspection import load_columns


DATABASE_TS_PATH = Path(__file__).resolve().parents[1] / "src" / "database.ts"


@dataclass
class ColumnDiff:
    table: str
    type: str
    missingFromTs: list[str]
    missingFromRw: list[str]


@dataclass
class Drift:
    tablesMissingFromTs: list[str]
    tablesMissingFromRw: list[str]
    columnDiffs: list[ColumnDiff]


def parse_database_ts(src: str) -> tuple[dict[str, str], dict[str, set[str]]]:
    db_match = re.search(r"export interface Database \{(?P<body>[\s\S]*?)\n\}", src)
    if not db_match:
        raise SystemExit("Database interface not found in src/database.ts")

    table_to_type: dict[str, str] = {}
    for match in re.finditer(r"^\s*'?([A-Za-z_][A-Za-z0-9_]*)'?\s*:\s*([A-Z][A-Za-z0-9_]*Row)\s*;", db_match["body"], re.M):
        table_to_type[match[1]] = match[2]

    type_to_columns: dict[str, set[str]] = {}
    for match in re.finditer(r"export interface ([A-Z][A-Za-z0-9_]*Row)\s*\{(?P<body>[\s\S]*?)\n\}", src):
        cols = {
            col[1]
            for col in re.finditer(r"^\s*'?([A-Za-z_][A-Za-z0-9_]*)'?\??:\s*", match["body"], re.M)
        }
        type_to_columns[match[1]] = cols
    return table_to_type, type_to_columns


def diff() -> Drift:
    engine = make_engine()
    rw_by_table: dict[str, set[str]] = {}
    for col in load_columns(engine):
        rw_by_table.setdefault(col.table_name, set()).add(col.column_name)

    table_to_type, type_to_columns = parse_database_ts(DATABASE_TS_PATH.read_text(encoding="utf-8"))

    missing_from_ts = sorted(table for table in rw_by_table if table not in table_to_type)
    missing_from_rw = sorted(table for table in table_to_type if table not in rw_by_table)
    column_diffs: list[ColumnDiff] = []
    for table, type_name in sorted(table_to_type.items()):
        if table not in rw_by_table or type_name not in type_to_columns:
            continue
        rw_cols = rw_by_table[table]
        ts_cols = type_to_columns[type_name]
        add = sorted(rw_cols - ts_cols)
        remove = sorted(ts_cols - rw_cols)
        if add or remove:
            column_diffs.append(ColumnDiff(table, type_name, add, remove))

    return Drift(missing_from_ts, missing_from_rw, column_diffs)


def render_text(drift: Drift) -> str:
    out = ["# graph-schema drift report", ""]
    out.append(f"Tables in RisingWave but missing from Database interface: {len(drift.tablesMissingFromTs)}")
    out.extend(f"  + {table}" for table in drift.tablesMissingFromTs)
    out.append("")
    out.append(f"Tables in Database interface but missing from RisingWave: {len(drift.tablesMissingFromRw)}")
    out.extend(f"  - {table}" for table in drift.tablesMissingFromRw)
    out.append("")
    out.append(f"Tables with column drift: {len(drift.columnDiffs)}")
    for item in drift.columnDiffs:
        out.append(f"  ~ {item.table} ({item.type})")
        out.extend(f"      + RW has, TS missing: {col}" for col in item.missingFromTs)
        out.extend(f"      - TS has, RW missing: {col}" for col in item.missingFromRw)
    out.append("")
    clean = not drift.tablesMissingFromTs and not drift.tablesMissingFromRw and not drift.columnDiffs
    out.append("OK: no drift detected." if clean else "DRIFT: see above.")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = diff()
    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print(render_text(result))
    if result.tablesMissingFromTs or result.tablesMissingFromRw or result.columnDiffs:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
