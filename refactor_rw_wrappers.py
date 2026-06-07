import glob
import os

def rewrite_rw_wrappers():
    files = glob.glob("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/*.py") + \
            glob.glob("40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/ingest/*.py")
    
    for path in files:
        with open(path, "r") as f:
            code = f.read()
            
        original_code = code

        if "def _rw_execute(sql" in code:
            code = code.replace("from kotodama.db_sync import sync_cursor\n", "")
            if "get_kotoba_client" not in code:
                code = code.replace("import logging", "import logging\nfrom kotodama.kotoba_datomic import get_kotoba_client")
                if "import logging" not in code:
                    code = "from kotodama.kotoba_datomic import get_kotoba_client\n" + code

            old_exec = """def _rw_execute(sql: str, params: tuple[Any, ...]) -> None:
    with sync_cursor() as cur:
        cur.execute(sql, params)"""
            new_exec = """def _rw_execute(sql: str, params: tuple[Any, ...] = ()) -> None:
    get_kotoba_client().q(sql, params)"""
            code = code.replace(old_exec, new_exec)
            
            # chat.py has slight variation: tuple[Any, ...] vs tuple[Any, ...] = ()
            old_exec2 = """def _rw_execute(sql: str, params: tuple[Any, ...] = ()) -> None:
    with sync_cursor() as cur:
        cur.execute(sql, params)"""
            code = code.replace(old_exec2, new_exec)

        if "def _rw_query(" in code:
            old_query = """def _rw_query(sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())"""
            new_query = """def _rw_query(sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    res = get_kotoba_client().q(sql, params)
    if not res: return []
    if isinstance(res[0], dict):
        return [tuple(r.values()) for r in res]
    return list(res)"""
            code = code.replace(old_query, new_query)
            
        if "def _rw_executemany(" in code:
            old_execmany = """def _rw_executemany(sql: str, rows: list[tuple[Any, ...]]) -> None:
    with sync_cursor() as cur:
        cur.executemany(sql, rows)"""
            new_execmany = """def _rw_executemany(sql: str, rows: list[tuple[Any, ...]]) -> None:
    c = get_kotoba_client()
    for r in rows: c.q(sql, r)"""
            code = code.replace(old_execmany, new_execmany)
            
        if code != original_code:
            with open(path, "w") as f:
                f.write(code)
            print(f"Patched {path}")

if __name__ == "__main__":
    rewrite_rw_wrappers()
