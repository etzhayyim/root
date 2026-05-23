import os
import re

def process_curpus2skill():
    path = "20-actors/magatama/py/src/pymagatama/ingest/curpus2skill.py"
    with open(path) as f:
        content = f.read()

    # Imports
    content = content.replace(
        "from pymagatama.db_sync import sync_cursor",
        "import sqlite3\nfrom contextlib import contextmanager\nimport os"
    )

    # SQLite sync_cursor logic
    sync_cursor_code = """

@contextmanager
def sync_cursor():
    db_dir = os.environ.get("ORGANISM_SQLITE_DIR", "/var/lib/etzhayyim/organism")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "ingest_curpus2skill.db")
    with sqlite3.connect(db_path) as conn:
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('''CREATE TABLE IF NOT EXISTS vertex_skill (
            vertex_id TEXT PRIMARY KEY, label TEXT, name TEXT, alt_labels TEXT, source_license TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS vertex_legal_corpus_document (
            vertex_id TEXT PRIMARY KEY, title TEXT, body_text TEXT, topic_tags_csv TEXT, owner_did TEXT, source_id TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS vertex_houbun_article (
            vertex_id TEXT PRIMARY KEY, title TEXT, text TEXT, article_no TEXT, owner_did TEXT, source_url TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS vertex_domain_knowledge_chunk (
            vertex_id TEXT PRIMARY KEY, document_vid TEXT, chunk_text TEXT, keywords TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS vertex_domain_knowledge_document (
            vertex_id TEXT PRIMARY KEY, title TEXT, owner_did TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS vertex_corpus_skill_extraction_run (
            vertex_id TEXT PRIMARY KEY, sensitivity_ord INTEGER, owner_did TEXT, rkey TEXT, repo TEXT, label TEXT, source_table TEXT, source_actor_did TEXT, extractor_version TEXT, model_id TEXT, params_json TEXT, corpus_limit INTEGER, skill_limit INTEGER, min_score REAL, matched_documents INTEGER, emitted_edges INTEGER, status TEXT, started_at TEXT, finished_at TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS edge_corpus_skill_evidence (
            edge_id TEXT PRIMARY KEY, corpus_vertex_id TEXT, corpus_table TEXT, skill_id TEXT, extraction_run_id TEXT, source_actor_did TEXT, match_kind TEXT, score REAL, evidence_text TEXT, evidence_start INTEGER, evidence_end INTEGER, source TEXT, source_license TEXT, ingested_at TEXT, props TEXT
        )''')
        yield conn.cursor()
"""
    content = content.replace("VERSION = \"curpus2skill-langserver-v0.1.0\"", sync_cursor_code + "\nVERSION = \"curpus2skill-langserver-v0.1.0\"")

    # Replace insert_run query
    content = re.sub(
        r"INSERT INTO vertex_corpus_skill_extraction_run \((.*?)\)\n\s*SELECT %s,%s::BIGINT,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::BIGINT,\n\s*%s::BIGINT,%s::DOUBLE PRECISION,%s::BIGINT,%s::BIGINT,\n\s*%s,%s,%s\n\s*WHERE NOT EXISTS \(\n\s*SELECT 1 FROM vertex_corpus_skill_extraction_run WHERE vertex_id = %s\n\s*\)",
        r"INSERT OR IGNORE INTO vertex_corpus_skill_extraction_run (\1)\n            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        content,
        flags=re.DOTALL
    )

    # Remove the extra `run["vertex_id"]` from args in insert_run
    content = content.replace(
        "run[\"finished_at\"], run[\"vertex_id\"],",
        "run[\"finished_at\"],"
    )

    # Replace insert_edge query
    content = re.sub(
        r"INSERT INTO edge_corpus_skill_evidence \((.*?)\)\n\s*SELECT %s,%s,%s,%s,%s,%s,%s,%s::DOUBLE PRECISION,%s,\n\s*%s::BIGINT,%s::BIGINT,%s,%s,%s,%s\n\s*WHERE NOT EXISTS \(\n\s*SELECT 1 FROM edge_corpus_skill_evidence WHERE edge_id = %s\n\s*\)",
        r"INSERT OR IGNORE INTO edge_corpus_skill_evidence (\1)\n            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        content,
        flags=re.DOTALL
    )

    # Remove the extra `edge_id` from args in insert_edge
    content = content.replace(
        "ensure_ascii=False),\n                edge_id,\n            )",
        "ensure_ascii=False),\n            )"
    )

    with open(path, "w") as f:
        f.write(content)

process_curpus2skill()
