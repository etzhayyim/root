import os
import re

def process_houbun():
    path = "20-actors/magatama/py/src/pymagatama/ingest/houbun.py"
    with open(path) as f:
        content = f.read()

    # Imports
    content = content.replace(
        "from pymagatama.db_sync import sync_cursor",
        "import sqlite3\nfrom contextlib import contextmanager"
    )

    # SQLite sync_cursor logic
    sync_cursor_code = """

@contextmanager
def sync_cursor():
    db_dir = os.environ.get("ORGANISM_SQLITE_DIR", "/var/lib/etzhayyim/organism")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "ingest_houbun.db")
    with sqlite3.connect(db_path) as conn:
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('''CREATE TABLE IF NOT EXISTS vertex_houbun_statute (
            vertex_id TEXT PRIMARY KEY, created_date TEXT, sensitivity_ord INTEGER, owner_did TEXT,
            rkey TEXT, repo TEXT, jurisdiction TEXT, statute_id TEXT, title TEXT, title_native TEXT,
            statute_type TEXT, enacted_date TEXT, effective_date TEXT, repealed_date TEXT, source TEXT,
            source_url TEXT, license TEXT, language TEXT, article_count INTEGER, last_verified TEXT,
            created_at TEXT, org_id TEXT, user_id TEXT, actor_id TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS vertex_houbun_article (
            vertex_id TEXT PRIMARY KEY, created_date TEXT, sensitivity_ord INTEGER, owner_did TEXT,
            rkey TEXT, repo TEXT, statute_ref TEXT, article_no TEXT, section TEXT, title TEXT,
            text TEXT, language TEXT, article_did TEXT, blake3_hash TEXT, amended_at TEXT,
            source_url TEXT, created_at TEXT, org_id TEXT, user_id TEXT, actor_id TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS edge_houbun_statute_article (
            edge_id TEXT PRIMARY KEY, src_vid TEXT, dst_vid TEXT, created_date TEXT,
            sensitivity_ord INTEGER, owner_did TEXT, article_no TEXT, order_key INTEGER,
            created_at TEXT, org_id TEXT, user_id TEXT, actor_id TEXT
        )''')
        yield conn.cursor()
"""
    content = content.replace("ACTOR_DID = \"did:web:houbun.etzhayyim.com\"", sync_cursor_code + "\nACTOR_DID = \"did:web:houbun.etzhayyim.com\"")

    # Replace _insert_ignore implementation
    old_insert = """def _insert_ignore(cur: Any, table: str, id_col: str, values: dict[str, Any]) -> int:
    clean = {k: v for k, v in values.items() if v is not None}
    cols = list(clean)
    placeholders = ", ".join(["%s"] * len(cols))
    cur.execute(
        f"INSERT INTO {table} ({', '.join(cols)}) "
        f"SELECT {placeholders} "
        f"WHERE NOT EXISTS (SELECT 1 FROM {table} WHERE {id_col} = %s)",
        (*[clean[c] for c in cols], clean[id_col]),
    )
    return int(cur.rowcount or 0)"""
    new_insert = """def _insert_ignore(cur: Any, table: str, id_col: str, values: dict[str, Any]) -> int:
    clean = {k: v for k, v in values.items() if v is not None}
    cols = list(clean)
    placeholders = ", ".join(["?"] * len(cols))
    cur.execute(
        f"INSERT OR IGNORE INTO {table} ({', '.join(cols)}) "
        f"VALUES ({placeholders})",
        (*[clean[c] for c in cols],),
    )
    return int(cur.rowcount or 0)"""
    content = content.replace(old_insert, new_insert)

    # Replace %s with ? for standard queries
    content = content.replace("= %s", "= ?")

    # In _write_payload_usa, _write_payload, _write_payload_chn, there's an UPDATE query
    content = content.replace(
        "SET title = %s,\n                   title_native = %s,\n                   article_count = %s,\n                   last_verified = %s\n             WHERE vertex_id = %s",
        "SET title = ?,\n                   title_native = ?,\n                   article_count = ?,\n                   last_verified = ?\n             WHERE vertex_id = ?"
    )

    with open(path, "w") as f:
        f.write(content)

process_houbun()
