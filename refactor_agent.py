import os
import glob
import re

def refactor_agent_economy():
    path = "20-actors/magatama/py/src/pymagatama/primitives/agent_economy.py"
    with open(path, "r") as f:
        code = f.read()

    code = code.replace("from pymagatama.db_sync import sync_cursor", "from pymagatama.kotoba_datomic import get_kotoba_client")

    old_insert = """def _insert(table: str, row: dict[str, Any], *, dry_run: bool = False) -> None:
    if dry_run:
        return
    columns = list(row)
    placeholders = ", ".join(["%s"] * len(columns))
    names = ", ".join(columns)
    values = tuple(
        _db_ts(_parse_ts(row[c])) if c in TIMESTAMP_COLUMNS and row[c] is not None else row[c]
        for c in columns
    )
    with sync_cursor() as cur:
        cur.execute(
            f"INSERT INTO {table} ({names}) VALUES ({placeholders})",  # noqa: S608
            values,
        )"""

    new_insert = """def _insert(table: str, row: dict[str, Any], *, dry_run: bool = False) -> None:
    if dry_run:
        return
    client = get_kotoba_client()
    formatted_row = {
        c: _db_ts(_parse_ts(row[c])) if c in TIMESTAMP_COLUMNS and row[c] is not None else row[c]
        for c in row
    }
    client.insert_row(table, formatted_row)"""

    code = code.replace(old_insert, new_insert)

    # replace fetch lease
    code = re.sub(
        r'with sync_cursor\(\) as cur:\n\s+cur\.execute\(\n\s+f"""(.*?)""",\n\s+\(_db_ts\(cutoff\),\),\n\s+\)\n\s+columns = \[desc\[0\] for desc in cur\.description or \[\]\]\n\s+return \[dict\(zip\(columns, row, strict=False\)\) for row in cur\.fetchall\(\)\]',
        r'client = get_kotoba_client()\n    return client.q(f"""\1""", (_db_ts(cutoff),))',
        code, flags=re.DOTALL
    )

    # replace fetch profile
    code = re.sub(
        r'with sync_cursor\(\) as cur:\n\s+cur\.execute\(\n\s+f"""(.*?)""",\n\s+\)\n\s+columns = \[desc\[0\] for desc in cur\.description or \[\]\]\n\s+return \[dict\(zip\(columns, row, strict=False\)\) for row in cur\.fetchall\(\)\]',
        r'client = get_kotoba_client()\n    return client.q(f"""\1""")',
        code, flags=re.DOTALL
    )

    with open(path, "w") as f:
        f.write(code)
    print("Refactored agent_economy.py")

if __name__ == "__main__":
    refactor_agent_economy()
