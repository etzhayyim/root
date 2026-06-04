#!/usr/bin/env python3
"""Apply Kysely migrations to RisingWave directly via psycopg2.

Extracts SQL statements from the `sql\`...\`` template literals in the
migration .ts files and executes them in order. This is a standalone
runner since Kysely's db:migrate requires ts-node + @etzhayyim/migrate-schema-to-kysely
which isn't set up in this repo.

Idempotent: all CREATE TABLE / MV statements use IF NOT EXISTS.

Usage:
  python3 30-graph/graph-schema/scripts/apply-migrations.py [--skip 0003]
  python3 30-graph/graph-schema/scripts/apply-migrations.py --drop-all  # clean slate
"""

import argparse
import os
import re
import sys
from pathlib import Path

import psycopg2

RW_HOST = os.environ.get("RW_HOST", "<vendor-rw-host-deprecated>")
RW_PORT = int(os.environ.get("RW_PORT", "4566"))
MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


def normalize_for_risingwave(sql: str) -> str:
    """Adjust SQL for RisingWave compatibility.

    RisingWave 2.8 does NOT support VARCHAR(n) length parameter — VARCHAR must be
    used bare. Strip all (n) from VARCHAR/CHARACTER VARYING declarations.
    """
    # VARCHAR(512) → VARCHAR, CHARACTER VARYING(1024) → CHARACTER VARYING
    sql = re.sub(r"(VARCHAR|CHARACTER\s+VARYING)\s*\(\s*\d+\s*\)", r"\1", sql, flags=re.IGNORECASE)
    return sql


def extract_sql_statements(ts_path: Path) -> list[str]:
    """Extract SQL statements from Kysely migration template literals.

    Matches: sql`...`.execute(db) or sql`...`.compile(db) or db.executeQuery(sql`...`.compile(db))
    Returns raw SQL strings inside the backticks (for the up() function only).
    """
    content = ts_path.read_text()

    # Find the up() function body
    up_match = re.search(
        r"export async function up\(db[^{]*\{(.*?)^\}",
        content,
        re.DOTALL | re.MULTILINE,
    )
    if not up_match:
        return []
    up_body = up_match.group(1)

    # Extract all sql`...` template literals (non-greedy)
    # Note: the backticks may contain newlines and template interpolation ${...}
    statements = []
    i = 0
    while True:
        sql_pos = up_body.find("sql`", i)
        if sql_pos < 0:
            break
        start = sql_pos + 4
        # Find matching closing backtick (handle nested template interpolation)
        depth = 0
        j = start
        while j < len(up_body):
            ch = up_body[j]
            if ch == "`" and depth == 0:
                break
            if ch == "$" and j + 1 < len(up_body) and up_body[j + 1] == "{":
                depth += 1
                j += 2
                continue
            if ch == "}" and depth > 0:
                depth -= 1
            j += 1
        stmt = up_body[start:j].strip()
        if stmt:
            statements.append(normalize_for_risingwave(stmt))
        i = j + 1
    return statements


def connect():
    return psycopg2.connect(
        host=RW_HOST, port=RW_PORT, user="root", database="dev",
        connect_timeout=30,
        keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=9,
    )


def drop_all_public(conn):
    """Drop all tables, MVs, sinks, sources, connections in public schema."""
    print("=== Drop all public objects ===")
    with conn.cursor() as cur:
        # Drop sinks
        cur.execute("SELECT name FROM rw_sinks")
        sinks = [r[0] for r in cur.fetchall() if not r[0].startswith("__")]
        for s in sinks:
            try:
                cur.execute(f'DROP SINK IF EXISTS "{s}"')
                print(f"  DROP SINK {s}")
            except Exception as e:
                print(f"  DROP SINK {s}: {str(e)[:100]}")

        # Drop MVs (CASCADE to handle dependencies)
        cur.execute("""
            SELECT m.name FROM rw_materialized_views m
            JOIN rw_schemas s ON m.schema_id = s.id
            WHERE s.name = 'public'
        """)
        mvs = [r[0] for r in cur.fetchall()]
        for m in mvs:
            try:
                cur.execute(f'DROP MATERIALIZED VIEW IF EXISTS "{m}" CASCADE')
                print(f"  DROP MV {m}")
            except Exception as e:
                print(f"  DROP MV {m}: {str(e)[:100]}")

        # Drop sources
        cur.execute("SELECT name FROM rw_sources")
        srcs = [r[0] for r in cur.fetchall() if not r[0].startswith("__")]
        for src in srcs:
            try:
                cur.execute(f'DROP SOURCE IF EXISTS "{src}" CASCADE')
                print(f"  DROP SOURCE {src}")
            except Exception as e:
                pass  # some may be auto-created for tables

        # Drop tables (CASCADE)
        cur.execute("""
            SELECT t.name FROM rw_tables t
            JOIN rw_schemas s ON t.schema_id = s.id
            WHERE s.name = 'public'
        """)
        tables = [r[0] for r in cur.fetchall()]
        dropped = 0
        for t in tables:
            try:
                cur.execute(f'DROP TABLE IF EXISTS "{t}" CASCADE')
                dropped += 1
            except Exception as e:
                print(f"  DROP TABLE {t}: {str(e)[:100]}")
        print(f"  Dropped {dropped}/{len(tables)} tables")

        # Drop connections
        try:
            cur.execute("SELECT name FROM rw_connections")
            conns = [r[0] for r in cur.fetchall()]
            for c in conns:
                try:
                    cur.execute(f'DROP CONNECTION IF EXISTS "{c}"')
                    print(f"  DROP CONNECTION {c}")
                except Exception as e:
                    print(f"  DROP CONNECTION {c}: {str(e)[:100]}")
        except Exception as e:
            print(f"  rw_connections query: {str(e)[:100]}")


def apply_migration(conn, ts_path: Path):
    print(f"\n=== Apply {ts_path.name} ===")
    stmts = extract_sql_statements(ts_path)
    print(f"  {len(stmts)} statements")
    ok = 0
    err = 0
    for i, stmt in enumerate(stmts, 1):
        # Skip statements with unresolved template interpolation (e.g., ${sql.raw(...)})
        if "${" in stmt:
            print(f"  [{i}] SKIP (template interpolation): {stmt.splitlines()[0][:80]}")
            continue
        try:
            with conn.cursor() as cur:
                cur.execute(stmt)
            ok += 1
        except Exception as e:
            err += 1
            first_line = stmt.splitlines()[0][:80]
            print(f"  [{i}] ERR: {first_line}")
            print(f"       {str(e)[:200]}")
    print(f"  {ok}/{len(stmts)} OK, {err} errors")
    return ok, err


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--drop-all", action="store_true",
                   help="DROP all public schema objects first")
    p.add_argument("--skip", action="append", default=["0003"],
                   help="Migration numbers to skip (default: 0003 iceberg)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    migrations = sorted(MIGRATIONS_DIR.glob("*.ts"))
    print(f"Migrations available: {len(migrations)}")
    for m in migrations:
        skip = any(s in m.name for s in args.skip)
        marker = "SKIP" if skip else "APPLY"
        print(f"  [{marker}] {m.name}")

    if args.dry_run:
        for m in migrations:
            if any(s in m.name for s in args.skip):
                continue
            stmts = extract_sql_statements(m)
            print(f"\n{m.name}: {len(stmts)} statements extracted")
            for s in stmts[:2]:
                print(f"  sample: {s[:100]}")
        return

    print(f"\nConnecting {RW_HOST}:{RW_PORT}...")
    conn = connect()
    conn.autocommit = True
    print("  OK")

    with conn.cursor() as cur:
        cur.execute("SET statement_timeout = 0")

    if args.drop_all:
        drop_all_public(conn)

    total_ok = 0
    total_err = 0
    for m in migrations:
        if any(s in m.name for s in args.skip):
            print(f"\n=== Skip {m.name} ===")
            continue
        ok, err = apply_migration(conn, m)
        total_ok += ok
        total_err += err

    print(f"\n=== Total: {total_ok} OK, {total_err} errors ===")

    # Final sanity
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM rw_tables t
            JOIN rw_schemas s ON t.schema_id = s.id WHERE s.name='public'
        """)
        print(f"  tables in public: {cur.fetchone()[0]}")
        cur.execute("""
            SELECT COUNT(*) FROM rw_materialized_views m
            JOIN rw_schemas s ON m.schema_id = s.id WHERE s.name='public'
        """)
        print(f"  MVs in public: {cur.fetchone()[0]}")

    conn.close()


if __name__ == "__main__":
    main()
