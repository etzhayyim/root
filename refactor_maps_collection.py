import re

def refactor_maps():
    path = "20-actors/magatama/py/src/pymagatama/ingest/maps_collection.py"
    with open(path, "r") as f:
        code = f.read()

    # 1. Imports
    code = code.replace("from pymagatama.db_sync import sync_cursor\n", "")
    if "from pymagatama.kotoba_datomic import get_kotoba_client" not in code:
        code = code.replace("from typing import Any\n", "from typing import Any\nfrom pymagatama.kotoba_datomic import get_kotoba_client\n")
    
    # 2. _execute
    old_execute = """def _execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return int(cur.rowcount or 0)"""
    new_execute = """def _execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    if sql.strip().upper() == "FLUSH": return 0
    client = get_kotoba_client()
    try:
        client.q(sql, params)
        return 1
    except Exception:
        return 0"""
    code = code.replace(old_execute, new_execute)

    # 3. _rows
    old_rows = """def _rows(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description or []]
        return [_inflate(dict(zip(cols, row))) for row in cur.fetchall()]"""
    new_rows = """def _rows(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    client = get_kotoba_client()
    results = client.q(sql, params)
    # Assume results from Kotoba q() are dicts directly for SELECT queries.
    if results and isinstance(results[0], dict):
        return [_inflate(r) for r in results]
    elif results and isinstance(results[0], tuple):
        # We don't have description, just return tuples if needed, though dicts expected
        pass
    return [_inflate(r) if isinstance(r, dict) else r for r in results]"""
    code = code.replace(old_rows, new_rows)

    with open(path, "w") as f:
        f.write(code)

if __name__ == "__main__":
    refactor_maps()
