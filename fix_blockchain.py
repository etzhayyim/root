import os
import re

def process_blockchain():
    path = "20-actors/magatama/py/src/pymagatama/ingest/blockchain.py"
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
    db_path = os.path.join(db_dir, "ingest_blockchain.db")
    with sqlite3.connect(db_path) as conn:
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('''CREATE TABLE IF NOT EXISTS vertex_ingest_cursor (
            vertex_id TEXT PRIMARY KEY,
            cursor_value TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS vertex_blockchain_actor (
            vertex_id TEXT PRIMARY KEY, _seq INTEGER, created_date TEXT, sensitivity_ord INTEGER, owner_did TEXT,
            rkey TEXT, repo TEXT, label TEXT, did TEXT, chain TEXT, address TEXT, name TEXT, balance INTEGER,
            total_received INTEGER, total_sent INTEGER, tx_count INTEGER, unconfirmed_tx_count INTEGER,
            risk_score REAL, source TEXT, observed_at TEXT, props TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS vertex_blockchain_block (
            vertex_id TEXT PRIMARY KEY, _seq INTEGER, created_date TEXT, sensitivity_ord INTEGER, owner_did TEXT,
            chain TEXT, source_id TEXT, height INTEGER, block_hash TEXT, parent_hash TEXT, block_time TEXT,
            tx_count INTEGER, raw_sha256 TEXT, raw_json TEXT, canonical_status TEXT, ingested_at TEXT, run_id TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS vertex_blockchain_tx (
            vertex_id TEXT PRIMARY KEY, _seq INTEGER, created_date TEXT, sensitivity_ord INTEGER, owner_did TEXT,
            chain TEXT, source_id TEXT, block_hash TEXT, block_height INTEGER, tx_hash TEXT, tx_index INTEGER,
            from_addr TEXT, to_addr TEXT, value_wei TEXT, raw_sha256 TEXT, raw_json TEXT, canonical_status TEXT, ingested_at TEXT, run_id TEXT
        )''')
        yield conn.cursor()
"""
    content = content.replace("OWNER_DID = \"did:web:blockchain.etzhayyim.com\"", sync_cursor_code + "\nOWNER_DID = \"did:web:blockchain.etzhayyim.com\"")

    # Replace %s with ?
    content = content.replace("= %s", "= ?")

    # Replace SELECT COUNT(*) FROM information_schema.tables
    content = content.replace(
        "SELECT COUNT(*) FROM information_schema.tables\n                WHERE table_name IN ('vertex_blockchain_block', 'vertex_blockchain_tx')",
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ('vertex_blockchain_block', 'vertex_blockchain_tx')"
    )

    # Rewrite INSERT INTO ... SELECT ... WHERE NOT EXISTS -> INSERT OR IGNORE INTO ... VALUES (...)
    content = re.sub(
        r"INSERT INTO (vertex_blockchain_actor) \((.*?)\)\n\s*SELECT %s, CAST\(NULL AS BIGINT\), CAST\(%s AS DATE\), CAST\(0 AS BIGINT\), %s,\n\s*%s, %s, %s, %s, %s, %s, %s, CAST\(0 AS BIGINT\),\n\s*CAST\(0 AS BIGINT\), CAST\(0 AS BIGINT\), CAST\(%s AS BIGINT\), CAST\(0 AS BIGINT\),\n\s*CAST\(0 AS DOUBLE PRECISION\), %s, %s, %s\n\s*WHERE NOT EXISTS \(SELECT 1 FROM vertex_blockchain_actor WHERE vertex_id = \?\)",
        r"INSERT OR IGNORE INTO \1 (\2)\n            VALUES (?, NULL, ?, 0, ?,\n                   ?, ?, ?, ?, ?, ?, ?, 0,\n                   0, 0, ?, 0,\n                   0.0, ?, ?, ?)",
        content,
        flags=re.DOTALL
    )

    content = re.sub(
        r"INSERT INTO (vertex_blockchain_block) \((.*?)\)\n\s*SELECT %s, CAST\(NULL AS BIGINT\), CAST\(%s AS DATE\), CAST\(0 AS BIGINT\), %s,\n\s*%s, %s, CAST\(%s AS BIGINT\), %s, %s, %s,\n\s*CAST\(%s AS BIGINT\), %s, %s, %s, %s,\n\s*%s\n\s*WHERE NOT EXISTS \(SELECT 1 FROM vertex_blockchain_block WHERE vertex_id = \?\)",
        r"INSERT OR IGNORE INTO \1 (\2)\n            VALUES (?, NULL, ?, 0, ?,\n                   ?, ?, ?, ?, ?, ?,\n                   ?, ?, ?, ?, ?,\n                   ?)",
        content,
        flags=re.DOTALL
    )

    content = re.sub(
        r"INSERT INTO (vertex_blockchain_tx) \((.*?)\)\n\s*SELECT %s, CAST\(NULL AS BIGINT\), CAST\(%s AS DATE\), CAST\(0 AS BIGINT\), %s,\n\s*%s, %s, %s, CAST\(%s AS BIGINT\), %s, CAST\(%s AS BIGINT\),\n\s*%s, %s, %s, %s, %s,\n\s*%s, %s, %s\n\s*WHERE NOT EXISTS \(SELECT 1 FROM vertex_blockchain_tx WHERE vertex_id = \?\)",
        r"INSERT OR IGNORE INTO \1 (\2)\n            VALUES (?, NULL, ?, 0, ?,\n                   ?, ?, ?, ?, ?, ?,\n                   ?, ?, ?, ?, ?,\n                   ?, ?, ?)",
        content,
        flags=re.DOTALL
    )

    # Remove the final ", row['vertex_id']" from the params list of the query executions.
    # ACTOR:
    content = content.replace(
        "props,\n                row[\"vertex_id\"],\n            )",
        "props,\n            )"
    )
    # BLOCK:
    content = content.replace(
        "row.get(\"run_id\", \"\"),\n                row[\"vertex_id\"],\n            )",
        "row.get(\"run_id\", \"\"),\n            )"
    )
    # TX:
    content = content.replace(
        "row.get(\"run_id\", \"\"),\n                row[\"vertex_id\"],\n            )",
        "row.get(\"run_id\", \"\"),\n            )"
    )

    with open(path, "w") as f:
        f.write(content)

process_blockchain()
