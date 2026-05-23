import os
import re

FILES = [
    "20-actors/magatama/py/src/pymagatama/ki_worker_main.py",
    "20-actors/magatama/py/src/pymagatama/kobo_worker_main.py",
    "20-actors/magatama/py/src/pymagatama/koke_worker_main.py",
    "20-actors/magatama/py/src/pymagatama/saikin_worker_main.py",
    "20-actors/magatama/py/src/pymagatama/myco_yeast_worker_main.py",
]

def port_file(path):
    with open(path, "r") as f:
        content = f.read()

    # 1. Imports
    content = re.sub(
        r"from pymagatama\.db_sync import fetch_all, fetch_one, sync_cursor\n",
        "",
        content
    )
    content = re.sub(
        r"from pymagatama\.db_sync import fetch_one, sync_cursor\n",
        "",
        content
    )
    if "import sqlite3" not in content:
        content = re.sub(
            r"(import signal\n)",
            r"\1import sqlite3\n",
            content
        )

    # Substrate imports
    records = []
    if "ki_worker" in path:
        records = ["KiAbsorbRecord", "KiArtifactRecord", "KiRingRecord"]
    elif "kobo_worker" in path:
        records = ["KoboAgentRecord", "KoboBuddingRecord", "HoushiSporeRecord", "HoushiCustodyRecord"]
    elif "koke_worker" in path:
        records = ["KokeFixationRecord", "HakkouFermentRecord", "KokeFlowRecord", "SaikinSignalRecord"]
    elif "saikin_worker" in path:
        records = ["SaikinSignalRecord", "SaikinTransferRecord", "SaikinColonyRecord", "SaikinMemberRecord", "KiAbsorbRecord"]
    elif "myco_yeast" in path:
        records = ["KabiAnastomosisRecord", "KabiHyphaRecord", "KabiNetworkRecord", "KoboAgentRecord", "KoboPrionRecord", "KoboBuddingRecord", "HoushiSporeRecord", "KinokoBlockRecord", "HakkouFermentRecord"]

    records_str = ", ".join(records)
    import_stmt = f"from pymagatama.primitives.active_inference_substrate import select_belief_store, {records_str}\n"

    content = re.sub(
        r"(from pymagatama\.local_agent_env import load_env_file, load_keychain_secret\n)",
        import_stmt + r"\1",
        content
    )

    # 2. _run queries
    # Replace fetch_one/fetch_all with store._conn()
    def replace_fetch_one(m):
        var_name = m.group(1)
        query = m.group(2)
        args = m.group(3)
        return f"""        store = select_belief_store()
        with store._conn() as conn:
            conn.row_factory = sqlite3.Row
            try:
                {var_name} = conn.execute(
{query},
                    {args}
                ).fetchone()
            except sqlite3.OperationalError:
                {var_name} = None"""

    def replace_fetch_all(m):
        var_name = m.group(1)
        query = m.group(2)
        args = m.group(3)
        return f"""        store = select_belief_store()
        with store._conn() as conn:
            conn.row_factory = sqlite3.Row
            try:
                {var_name} = conn.execute(
{query},
                    {args}
                ).fetchall()
            except sqlite3.OperationalError:
                {var_name} = []"""

    # We need to manually fix fetch_one/fetch_all calls. They look like:
    # row = fetch_one(\n            "SELECT ...",\n            (args,),\n        )
    # The regex might be tricky. Let's write a simple AST rewriter or just use manual string replacement scripts tailored for each file.

    # Actually, the prompt allows us to write the files directly. Let's do manual replace.

    pass

if __name__ == "__main__":
    pass
