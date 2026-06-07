import re
import sys

def patch(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # 1. Remove psycopg imports, DB helpers, and vec_literal
    content = re.sub(r'import psycopg\nimport psycopg\.rows\n', '', content)
    content = re.sub(r'RW_DSN\s*=\s*os\.environ\.get.*?\n', '', content)
    
    db_helpers_pattern = r'# ─────────────────────────────────────────────────────────────\n# DB helpers \(psycopg3 async — one connection per call\)\n# ─────────────────────────────────────────────────────────────.*?# ─────────────────────────────────────────────────────────────\n# bge-m3 embed model'
    content = re.sub(db_helpers_pattern, '# ─────────────────────────────────────────────────────────────\n# bge-m3 embed model', content, flags=re.DOTALL)
    
    vec_literal_pattern = r'def _vec_literal\(embedding: list\[float\]\) -> str:.*?return "\\[" \+ ","\.join\(f"\{x:\.8f\}" for x in embedding\) \+ "\\]"\n\n\n'
    content = re.sub(vec_literal_pattern, '\n', content, flags=re.DOTALL)

    # 2. _ingest_dedupe
    ingest_dedupe_old = """async def _ingest_dedupe(state: IngestState) -> IngestState:
    row = await _fetchone(
        "SELECT vertex_id FROM vertex_legal_corpus_document"
        " WHERE source_id = %s AND canonical_uri = %s LIMIT 1",
        (state["source_id"], state["canonical_uri"]),
    )
    if row:
        return {**state, "vertex_id": row["vertex_id"], "already_known": True}
    return {**state, "vertex_id": _vertex_id(state["source_id"], state["canonical_uri"]), "already_known": False}"""
    ingest_dedupe_new = """async def _ingest_dedupe(state: IngestState) -> IngestState:
    from pymagatama.kotoba_datomic import get_kotoba_client
    client = get_kotoba_client()
    rows = client.q(
        "SELECT vertex_id FROM vertex_legal_corpus_document"
        " WHERE source_id = %s AND canonical_uri = %s LIMIT 1",
        (state["source_id"], state["canonical_uri"]),
    )
    row = rows[0] if rows else None
    if row:
        return {**state, "vertex_id": row["vertex_id"], "already_known": True}
    return {**state, "vertex_id": _vertex_id(state["source_id"], state["canonical_uri"]), "already_known": False}"""
    content = content.replace(ingest_dedupe_old, ingest_dedupe_new)

    # 3. _ingest_insert
    ingest_insert_old = """async def _ingest_insert(state: IngestState) -> IngestState:
    if state["already_known"]:
        return state
    try:
        await _execute(
            \"\"\"
            INSERT INTO vertex_legal_corpus_document
              (vertex_id, source_id, canonical_uri, document_type, jurisdiction,
               court, court_did, language_code, title, citation,
               decided_at, published_at, fetched_at, body_text, body_uri,
               topic_tags_csv, sensitivity_ord, owner_did, created_at)
            VALUES
              (%s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s)
            \"\"\",
            (
                state["vertex_id"], state["source_id"], state["canonical_uri"],
                state["document_type"], state.get("jurisdiction"),
                state.get("court"), state.get("court_did"), state["language_code"],
                state["title"], state.get("citation"),
                state.get("decided_at"), state.get("published_at"), state["fetched_at"],
                state.get("body_text"), state.get("body_uri"),
                state.get("topic_tags_csv"), state.get("sensitivity_ord", 1),
                OWNER_DID, state["fetched_at"],
            ),
        )
    except Exception as exc:
        return {**state, "error": str(exc)}
    return state"""
    ingest_insert_new = """async def _ingest_insert(state: IngestState) -> IngestState:
    if state["already_known"]:
        return state
    try:
        from pymagatama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        client.insert_row("vertex_legal_corpus_document", {
            "vertex_id": state["vertex_id"],
            "source_id": state["source_id"],
            "canonical_uri": state["canonical_uri"],
            "document_type": state["document_type"],
            "jurisdiction": state.get("jurisdiction"),
            "court": state.get("court"),
            "court_did": state.get("court_did"),
            "language_code": state["language_code"],
            "title": state["title"],
            "citation": state.get("citation"),
            "decided_at": state.get("decided_at"),
            "published_at": state.get("published_at"),
            "fetched_at": state["fetched_at"],
            "body_text": state.get("body_text"),
            "body_uri": state.get("body_uri"),
            "topic_tags_csv": state.get("topic_tags_csv"),
            "sensitivity_ord": state.get("sensitivity_ord", 1),
            "owner_did": OWNER_DID,
            "created_at": state["fetched_at"]
        })
    except Exception as exc:
        return {**state, "error": str(exc)}
    return state"""
    content = content.replace(ingest_insert_old, ingest_insert_new)

    # 4. _embed_load
    embed_load_old = """async def _embed_load(state: EmbedState) -> EmbedState:
    row = await _fetchone(
        "SELECT vertex_id, body_text FROM vertex_legal_corpus_document"
        " WHERE vertex_id = %s LIMIT 1",
        (state["vertex_id"],),
    )
    if not row or not row.get("body_text"):
        return {**state, "error": "no body_text found"}
    return {**state, "body_text": row["body_text"]}"""
    embed_load_new = """async def _embed_load(state: EmbedState) -> EmbedState:
    from pymagatama.kotoba_datomic import get_kotoba_client
    client = get_kotoba_client()
    rows = client.q(
        "SELECT vertex_id, body_text FROM vertex_legal_corpus_document"
        " WHERE vertex_id = %s LIMIT 1",
        (state["vertex_id"],),
    )
    row = rows[0] if rows else None
    if not row or not row.get("body_text"):
        return {**state, "error": "no body_text found"}
    return {**state, "body_text": row["body_text"]}"""
    content = content.replace(embed_load_old, embed_load_new)

    # 5. _embed_write
    embed_write_old = """async def _embed_write(state: EmbedState) -> EmbedState:
    if not state.get("embedding"):
        return {**state, "updated": False}
    vec = _vec_literal(state["embedding"])
    try:
        await _execute(
            f\"\"\"
            UPDATE vertex_legal_corpus_document
               SET embedding_vec = '{vec}'::vector(1024),
                   embedding_dim = %s,
                   embedding_model = 'BAAI/bge-m3',
                   embedding_at = now()
             WHERE vertex_id = %s
            \"\"\",
            (state["dim"], state["vertex_id"]),
        )
    except Exception as exc:
        return {**state, "updated": False, "error": str(exc)}
    return {**state, "updated": True}"""
    embed_write_new = """async def _embed_write(state: EmbedState) -> EmbedState:
    if not state.get("embedding"):
        return {**state, "updated": False}
    try:
        from pymagatama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        client.q(
            \"\"\"
            UPDATE vertex_legal_corpus_document
               SET embedding_vec = %s,
                   embedding_dim = %s,
                   embedding_model = 'BAAI/bge-m3',
                   embedding_at = now()
             WHERE vertex_id = %s
            \"\"\",
            (state["embedding"], state["dim"], state["vertex_id"]),
        )
    except Exception as exc:
        return {**state, "updated": False, "error": str(exc)}
    return {**state, "updated": True}"""
    content = content.replace(embed_write_old, embed_write_new)

    # 6. _search_run
    search_run_old = """    vec = _vec_literal(embedding)
    limit_i = max(1, min(int(state.get("limit") or 10), 100))

    where_parts = ["embedding_vec IS NOT NULL"]
    if state.get("jurisdiction"):
        where_parts.append(f"jurisdiction = '{state['jurisdiction'].replace(chr(39), '')}'")
    if state.get("document_type"):
        where_parts.append(f"document_type = '{state['document_type'].replace(chr(39), '')}'")
    if state.get("language_code"):
        where_parts.append(f"language_code = '{state['language_code'].replace(chr(39), '')}'")
    if state.get("decided_after"):
        where_parts.append(f"decided_at >= '{state['decided_after'].replace(chr(39), '')}'")
    if state.get("decided_before"):
        where_parts.append(f"decided_at < '{state['decided_before'].replace(chr(39), '')}'")
    where_sql = " AND ".join(where_parts)

    sql = f\"\"\"
        SELECT vertex_id, canonical_uri, title, court, jurisdiction,
               document_type, language_code, source_id,
               1 - (embedding_vec <=> '{vec}'::vector(1024)) AS score
          FROM vertex_legal_corpus_document
         WHERE {where_sql}
         ORDER BY embedding_vec <=> '{vec}'::vector(1024)
         LIMIT {limit_i}
    \"\"\"
    try:
        rows = await _fetchall(sql)
    except Exception as exc:
        return {**state, "hits": [], "hit_count": 0, "error": f"search failed: {exc}"}"""
    search_run_new = """    vec = embedding
    limit_i = max(1, min(int(state.get("limit") or 10), 100))

    where_parts = ["embedding_vec IS NOT NULL"]
    if state.get("jurisdiction"):
        where_parts.append(f"jurisdiction = '{state['jurisdiction'].replace(chr(39), '')}'")
    if state.get("document_type"):
        where_parts.append(f"document_type = '{state['document_type'].replace(chr(39), '')}'")
    if state.get("language_code"):
        where_parts.append(f"language_code = '{state['language_code'].replace(chr(39), '')}'")
    if state.get("decided_after"):
        where_parts.append(f"decided_at >= '{state['decided_after'].replace(chr(39), '')}'")
    if state.get("decided_before"):
        where_parts.append(f"decided_at < '{state['decided_before'].replace(chr(39), '')}'")
    where_sql = " AND ".join(where_parts)

    sql = f\"\"\"
        SELECT vertex_id, canonical_uri, title, court, jurisdiction,
               document_type, language_code, source_id,
               1 - (embedding_vec <=> %s) AS score
          FROM vertex_legal_corpus_document
         WHERE {where_sql}
         ORDER BY embedding_vec <=> %s
         LIMIT {limit_i}
    \"\"\"
    try:
        from pymagatama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        rows = client.q(sql, (vec, vec))
    except Exception as exc:
        return {**state, "hits": [], "hit_count": 0, "error": f"search failed: {exc}"}"""
    content = content.replace(search_run_old, search_run_new)

    # 7. _fae_write_body
    fae_write_body_old = """async def _fae_write_body(state: FetchAndEmbedState) -> FetchAndEmbedState:
    if not state.get("body_text"):
        return {**state, "body_updated": False}
    try:
        await _execute(
            "UPDATE vertex_legal_corpus_document SET body_text = %s WHERE vertex_id = %s",
            (state["body_text"], state["vertex_id"]),
        )
    except Exception as exc:
        return {**state, "body_updated": False, "error": str(exc)}
    return {**state, "body_updated": True}"""
    fae_write_body_new = """async def _fae_write_body(state: FetchAndEmbedState) -> FetchAndEmbedState:
    if not state.get("body_text"):
        return {**state, "body_updated": False}
    try:
        from pymagatama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        client.q(
            "UPDATE vertex_legal_corpus_document SET body_text = %s WHERE vertex_id = %s",
            (state["body_text"], state["vertex_id"]),
        )
    except Exception as exc:
        return {**state, "body_updated": False, "error": str(exc)}
    return {**state, "body_updated": True}"""
    content = content.replace(fae_write_body_old, fae_write_body_new)

    # 8. _fae_encode
    fae_encode_old = """async def _fae_encode(state: FetchAndEmbedState) -> FetchAndEmbedState:
    text = state.get("body_text") or ""
    if not text:
        # Fall back to title for docs without CELLAR XHTML (still searchable by title)
        row = await _fetchone(
            "SELECT title FROM vertex_legal_corpus_document WHERE vertex_id = %s LIMIT 1",
            (state["vertex_id"],),
        )
        text = (row["title"] if row else "") or ""
    if not text:
        return {**state, "embedding": [], "dim": 0}
    embedding = await _embed_text(text)
    return {**state, "embedding": embedding, "dim": len(embedding)}"""
    fae_encode_new = """async def _fae_encode(state: FetchAndEmbedState) -> FetchAndEmbedState:
    text = state.get("body_text") or ""
    if not text:
        # Fall back to title for docs without CELLAR XHTML (still searchable by title)
        from pymagatama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        rows = client.q(
            "SELECT title FROM vertex_legal_corpus_document WHERE vertex_id = %s LIMIT 1",
            (state["vertex_id"],),
        )
        row = rows[0] if rows else None
        text = (row["title"] if row else "") or ""
    if not text:
        return {**state, "embedding": [], "dim": 0}
    embedding = await _embed_text(text)
    return {**state, "embedding": embedding, "dim": len(embedding)}"""
    content = content.replace(fae_encode_old, fae_encode_new)

    # 9. _fae_write_embed
    fae_write_embed_old = """async def _fae_write_embed(state: FetchAndEmbedState) -> FetchAndEmbedState:
    if not state.get("embedding"):
        return {**state, "embed_updated": False}
    vec = _vec_literal(state["embedding"])
    try:
        await _execute(
            f\"\"\"
            UPDATE vertex_legal_corpus_document
               SET embedding_vec = '{vec}'::vector(1024),
                   embedding_dim = %s,
                   embedding_model = 'BAAI/bge-m3',
                   embedding_at = now()
             WHERE vertex_id = %s
            \"\"\",
            (state["dim"], state["vertex_id"]),
        )
    except Exception as exc:
        return {**state, "embed_updated": False, "error": str(exc)}
    return {**state, "embed_updated": True}"""
    fae_write_embed_new = """async def _fae_write_embed(state: FetchAndEmbedState) -> FetchAndEmbedState:
    if not state.get("embedding"):
        return {**state, "embed_updated": False}
    try:
        from pymagatama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        client.q(
            \"\"\"
            UPDATE vertex_legal_corpus_document
               SET embedding_vec = %s,
                   embedding_dim = %s,
                   embedding_model = 'BAAI/bge-m3',
                   embedding_at = now()
             WHERE vertex_id = %s
            \"\"\",
            (state["embedding"], state["dim"], state["vertex_id"]),
        )
    except Exception as exc:
        return {**state, "embed_updated": False, "error": str(exc)}
    return {**state, "embed_updated": True}"""
    content = content.replace(fae_write_embed_old, fae_write_embed_new)

    # 10. _cl_load_cursor
    cl_load_cursor_old = """async def _cl_load_cursor(state: FetchCourtListenerState) -> FetchCourtListenerState:
    row = await _fetchone(
        "SELECT last_cursor, secret_ref FROM vertex_legal_corpus_source"
        " WHERE source_id = 'courtlistener' LIMIT 1"
    )
    cursor = row["last_cursor"] if row else None
    secret = row["secret_ref"] if row else ""
    return {**state, "cursor": cursor, "secret_ref": secret}"""
    cl_load_cursor_new = """async def _cl_load_cursor(state: FetchCourtListenerState) -> FetchCourtListenerState:
    from pymagatama.kotoba_datomic import get_kotoba_client
    client = get_kotoba_client()
    rows = client.q(
        "SELECT last_cursor, secret_ref FROM vertex_legal_corpus_source"
        " WHERE source_id = 'courtlistener' LIMIT 1"
    )
    row = rows[0] if rows else None
    cursor = row["last_cursor"] if row else None
    secret = row["secret_ref"] if row else ""
    return {**state, "cursor": cursor, "secret_ref": secret}"""
    content = content.replace(cl_load_cursor_old, cl_load_cursor_new)

    # 11. _cl_advance_cursor
    cl_advance_cursor_old = """async def _cl_advance_cursor(state: FetchCourtListenerState) -> FetchCourtListenerState:
    now = _now()
    next_cur = state.get("next_cursor")
    if next_cur:
        try:
            await _execute(
                "UPDATE vertex_legal_corpus_source"
                " SET last_cursor = %s, last_fetched_at = %s"
                " WHERE source_id = 'courtlistener'",
                (next_cur, now),
            )
        except Exception as exc:
            return {**state, "error": str(exc)}
    return state"""
    cl_advance_cursor_new = """async def _cl_advance_cursor(state: FetchCourtListenerState) -> FetchCourtListenerState:
    now = _now()
    next_cur = state.get("next_cursor")
    if next_cur:
        try:
            from pymagatama.kotoba_datomic import get_kotoba_client
            client = get_kotoba_client()
            client.q(
                "UPDATE vertex_legal_corpus_source"
                " SET last_cursor = %s, last_fetched_at = %s"
                " WHERE source_id = 'courtlistener'",
                (next_cur, now),
            )
        except Exception as exc:
            return {**state, "error": str(exc)}
    return state"""
    content = content.replace(cl_advance_cursor_old, cl_advance_cursor_new)

    # 12. _canlii_load_key
    canlii_load_key_old = """async def _canlii_load_key(state: FetchCanLiiState) -> FetchCanLiiState:
    row = await _fetchone(
        "SELECT secret_ref FROM vertex_legal_corpus_source"
        " WHERE source_id = 'canlii' LIMIT 1"
    )
    key = row["secret_ref"] if row else ""
    return {**state, "canlii_key": key}"""
    canlii_load_key_new = """async def _canlii_load_key(state: FetchCanLiiState) -> FetchCanLiiState:
    from pymagatama.kotoba_datomic import get_kotoba_client
    client = get_kotoba_client()
    rows = client.q(
        "SELECT secret_ref FROM vertex_legal_corpus_source"
        " WHERE source_id = 'canlii' LIMIT 1"
    )
    row = rows[0] if rows else None
    key = row["secret_ref"] if row else ""
    return {**state, "canlii_key": key}"""
    content = content.replace(canlii_load_key_old, canlii_load_key_new)

    with open(file_path, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    patch(sys.argv[1])
