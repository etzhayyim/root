import os
import re

def process_site_common_crawl():
    path = "20-actors/magatama/py/src/pymagatama/ingest/site_common_crawl.py"
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
    db_path = os.path.join(db_dir, "ingest_site_common_crawl.db")
    with sqlite3.connect(db_path) as conn:
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('''CREATE TABLE IF NOT EXISTS mv_site_page_total (cnt INTEGER)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS vertex_page (vertex_id TEXT PRIMARY KEY, crawl TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS mv_site_job_total (cnt INTEGER)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS vertex_collection_job (vertex_id TEXT PRIMARY KEY)''')
        yield conn.cursor()
"""
    content = content.replace("ACTOR_DID = \"did:web:site.etzhayyim.com\"", sync_cursor_code + "\nACTOR_DID = \"did:web:site.etzhayyim.com\"")

    # Replace %s with ?
    content = content.replace("= %s", "= ?")

    with open(path, "w") as f:
        f.write(content)

process_site_common_crawl()
