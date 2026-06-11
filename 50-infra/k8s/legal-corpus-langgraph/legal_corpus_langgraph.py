"""legal-corpus LangGraph chains.

Replaces the Zeebe/pyzeebe BPMN-as-actor runtime for legal-corpus.etzhayyim.com
(ADR-0049, ADR-2605080600).  BPMN files under
00-contracts/bpmn/com/etzhayyim/legal-corpus/ remain as process contracts and
audit documents; this module is the runtime implementation.

Graphs:
  ingest_document_graph   — dedupe + INSERT vertex_legal_corpus_document
  embed_document_graph    — load body_text → bge-m3 → UPDATE embedding_vec
  search_document_graph   — embed query + inline-vec cosine search (RW quirk)
  fetch_and_embed_graph   — fetchBodyText → writeBody → embed → writeEmbed
  fetch_eurlex_graph      — EUR-Lex SPARQL → parallel ingest fan-out
  fetch_courtlistener_graph — CourtListener API → parallel ingest fan-out
  fetch_bailii_graph      — BAILII Atom → parallel ingest fan-out
  fetch_worldlii_graph    — WorldLii OAI-PMH → parallel ingest fan-out
  fetch_canlii_graph      — CanLII API → parallel ingest fan-out

CRITICAL (Kotoba/Datomic vector quirk):
  psycopg3 rejects ::vector(1024) as a prepared-statement parameter.
  All cosine-search and embedding-update queries inline the vector literal
  as a string: `'[x0,x1,...]'::vector(1024)`.
"""

from __future__ import annotations

import asyncio
import datetime
import html.parser
import json
import operator
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Annotated, Any, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

# ─────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────

OWNER_DID = "did:web:legal-corpus.etzhayyim.com"


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _vertex_id(source_id: str, canonical_uri: str) -> str:
    return (
        f"at://{OWNER_DID}/com.etzhayyim.apps.legal-corpus.document/"
        f"{source_id}:{canonical_uri}"
    )


# ─────────────────────────────────────────────────────────────
# bge-m3 embed model (lazy, process-level singleton)
# ─────────────────────────────────────────────────────────────

_embed_model: Any | None = None
_embed_lock: asyncio.Lock | None = None


async def _get_embed_model() -> Any:
    global _embed_model, _embed_lock
    if _embed_lock is None:
        _embed_lock = asyncio.Lock()
    async with _embed_lock:
        if _embed_model is None:
            from sentence_transformers import SentenceTransformer  # type: ignore[import]
            _embed_model = await asyncio.to_thread(SentenceTransformer, "BAAI/bge-m3")
    return _embed_model


async def _embed_text(text: str) -> list[float]:
    """Encode text with bge-m3, truncated to 2048 chars (~512 tokens)."""
    model = await _get_embed_model()
    return await asyncio.to_thread(
        lambda: model.encode(text[:2048], normalize_embeddings=True).tolist()
    )


def _vec_literal(embedding: list[float]) -> str:
    """Format float list as an inline Kotoba/Datomic vector literal.

    Kotoba/Datomic psycopg3 rejects ::vector(1024) in parameterized statements;
    the literal must be inlined directly in the SQL string.
    """
    return "[" + ",".join(f"{x:.8f}" for x in embedding) + "]"


# ─────────────────────────────────────────────────────────────
# 1. IngestDocument graph
#    Replaces: ingestDocument.bpmn (dedupe → INSERT → audit)
# ─────────────────────────────────────────────────────────────

class IngestState(TypedDict):
    source_id:      str
    canonical_uri:  str
    document_type:  str
    jurisdiction:   str | None
    court:          str | None
    court_did:      str | None
    language_code:  str
    title:          str
    citation:       str | None
    decided_at:     str | None
    published_at:   str | None
    fetched_at:     str
    body_text:      str | None
    body_uri:       str | None
    topic_tags_csv: str | None
    sensitivity_ord: int
    vertex_id:      str
    already_known:  bool
    error:          str | None


async def _ingest_dedupe(state: IngestState) -> IngestState:
    from kotodama.kotoba_datomic import get_kotoba_client
    client = get_kotoba_client()
    rows = client.q(
        "SELECT vertex_id FROM vertex_legal_corpus_document"
        " WHERE source_id = %s AND canonical_uri = %s LIMIT 1",
        (state["source_id"], state["canonical_uri"]),
    )
    row = rows[0] if rows else None
    if row:
        return {**state, "vertex_id": row["vertex_id"], "already_known": True}
    return {**state, "vertex_id": _vertex_id(state["source_id"], state["canonical_uri"]), "already_known": False}


async def _ingest_insert(state: IngestState) -> IngestState:
    if state["already_known"]:
        return state
    try:
        from kotodama.kotoba_datomic import get_kotoba_client
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
    return state


def _ingest_audit(state: IngestState) -> IngestState:
    # Structured audit log to stdout (captured by k8s logging)
    print(json.dumps({
        "action": "legal-corpus.ingestDocument",
        "actor": OWNER_DID,
        "vertexId": state["vertex_id"],
        "sourceId": state["source_id"],
        "canonicalUri": state["canonical_uri"],
        "alreadyKnown": state["already_known"],
        "error": state.get("error"),
    }))
    return state


def build_ingest_document_graph() -> Any:
    g = StateGraph(IngestState)
    g.add_node("dedupe",  _ingest_dedupe)
    g.add_node("insert",  _ingest_insert)
    g.add_node("audit",   _ingest_audit)
    g.set_entry_point("dedupe")
    g.add_edge("dedupe", "insert")
    g.add_edge("insert", "audit")
    g.add_edge("audit",  END)
    return g.compile()


# ─────────────────────────────────────────────────────────────
# 2. EmbedDocument graph
#    Replaces: embedDocument.bpmn (load → bge-m3 → UPDATE embedding_vec)
# ─────────────────────────────────────────────────────────────

class EmbedState(TypedDict):
    vertex_id:  str
    body_text:  str
    embedding:  list[float]
    dim:        int
    updated:    bool
    error:      str | None


async def _embed_load(state: EmbedState) -> EmbedState:
    from kotodama.kotoba_datomic import get_kotoba_client
    client = get_kotoba_client()
    rows = client.q(
        "SELECT vertex_id, body_text FROM vertex_legal_corpus_document"
        " WHERE vertex_id = %s LIMIT 1",
        (state["vertex_id"],),
    )
    row = rows[0] if rows else None
    if not row or not row.get("body_text"):
        return {**state, "error": "no body_text found"}
    return {**state, "body_text": row["body_text"]}


async def _embed_encode(state: EmbedState) -> EmbedState:
    if state.get("error") or not state.get("body_text"):
        return {**state, "embedding": [], "dim": 0}
    embedding = await _embed_text(state["body_text"])
    return {**state, "embedding": embedding, "dim": len(embedding)}


async def _embed_write(state: EmbedState) -> EmbedState:
    if not state.get("embedding"):
        return {**state, "updated": False}
    try:
        from kotodama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        client.q(
            """
            UPDATE vertex_legal_corpus_document
               SET embedding_vec = %s,
                   embedding_dim = %s,
                   embedding_model = 'BAAI/bge-m3',
                   embedding_at = now()
             WHERE vertex_id = %s
            """,
            (state["embedding"], state["dim"], state["vertex_id"]),
        )
    except Exception as exc:
        return {**state, "updated": False, "error": str(exc)}
    return {**state, "updated": True}


def build_embed_document_graph() -> Any:
    g = StateGraph(EmbedState)
    g.add_node("load",   _embed_load)
    g.add_node("encode", _embed_encode)
    g.add_node("write",  _embed_write)
    g.set_entry_point("load")
    g.add_edge("load",   "encode")
    g.add_edge("encode", "write")
    g.add_edge("write",  END)
    return g.compile()


# ─────────────────────────────────────────────────────────────
# 3. SearchDocument graph
#    Replaces: searchDocument.bpmn + legal.corpus.searchDocument handler
#    CRITICAL: vec literal inlined to avoid Kotoba/Datomic psycopg3 rejection
# ─────────────────────────────────────────────────────────────

class SearchState(TypedDict):
    query_text:    str
    jurisdiction:  str
    document_type: str
    language_code: str
    decided_after: str
    decided_before: str
    limit:         int
    hits:          list[dict]
    hit_count:     int
    error:         str | None


async def _search_run(state: SearchState) -> SearchState:
    if not state.get("query_text"):
        return {**state, "hits": [], "hit_count": 0, "error": "query_text required"}

    try:
        embedding = await _embed_text(state["query_text"])
    except Exception as exc:
        return {**state, "hits": [], "hit_count": 0, "error": f"embed failed: {exc}"}

    vec = embedding
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

    sql = f"""
        SELECT vertex_id, canonical_uri, title, court, jurisdiction,
               document_type, language_code, source_id,
               1 - (embedding_vec <=> %s) AS score
          FROM vertex_legal_corpus_document
         WHERE {where_sql}
         ORDER BY embedding_vec <=> %s
         LIMIT {limit_i}
    """
    try:
        from kotodama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        rows = client.q(sql, (vec, vec))
    except Exception as exc:
        return {**state, "hits": [], "hit_count": 0, "error": f"search failed: {exc}"}

    import decimal
    def _coerce(v: object) -> object:
        if isinstance(v, (datetime.date, datetime.datetime)):
            return v.isoformat()
        if isinstance(v, decimal.Decimal):
            return float(v)
        return v

    hits = [{k: _coerce(v) for k, v in row.items()} for row in rows]
    return {**state, "hits": hits, "hit_count": len(hits), "error": None}


def build_search_document_graph() -> Any:
    g = StateGraph(SearchState)
    g.add_node("search", _search_run)
    g.set_entry_point("search")
    g.add_edge("search", END)
    return g.compile()


# ─────────────────────────────────────────────────────────────
# 4. FetchAndEmbed graph
#    Replaces: fetchAndEmbed.bpmn (fetchBodyText → write → embed → write)
# ─────────────────────────────────────────────────────────────

class FetchAndEmbedState(TypedDict):
    vertex_id:    str
    canonical_uri: str
    source_id:    str
    body_text:    str
    embedding:    list[float]
    dim:          int
    body_updated: bool
    embed_updated: bool
    error:        str | None


async def _fae_fetch_body(state: FetchAndEmbedState) -> FetchAndEmbedState:
    """Fetch body text from canonical URI (EUR-Lex XHTML + SPARQL fallback)."""
    canonical_uri = state.get("canonical_uri", "")
    source_id     = state.get("source_id", "")

    if source_id == "eur-lex" or "publications.europa.eu" in canonical_uri:
        status, text = await asyncio.to_thread(_fetch_eur_lex_xhtml, canonical_uri)
        if status == 200 and text.strip():
            return {**state, "body_text": text, "error": None}
        if status in (404, 406):
            en_uri = await asyncio.to_thread(_sparql_en_expr, canonical_uri)
            if en_uri and en_uri != canonical_uri:
                status2, text2 = await asyncio.to_thread(_fetch_eur_lex_xhtml, en_uri)
                if status2 == 200 and text2.strip():
                    return {**state, "body_text": text2, "error": None}
        return {**state, "body_text": "", "error": f"eur-lex fetch {status}"}
    return {**state, "body_text": "", "error": f"unsupported sourceId={source_id!r}"}


async def _fae_write_body(state: FetchAndEmbedState) -> FetchAndEmbedState:
    if not state.get("body_text"):
        return {**state, "body_updated": False}
    try:
        from kotodama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        client.q(
            "UPDATE vertex_legal_corpus_document SET body_text = %s WHERE vertex_id = %s",
            (state["body_text"], state["vertex_id"]),
        )
    except Exception as exc:
        return {**state, "body_updated": False, "error": str(exc)}
    return {**state, "body_updated": True}


async def _fae_encode(state: FetchAndEmbedState) -> FetchAndEmbedState:
    text = state.get("body_text") or ""
    if not text:
        # Fall back to title for docs without CELLAR XHTML (still searchable by title)
        from kotodama.kotoba_datomic import get_kotoba_client
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
    return {**state, "embedding": embedding, "dim": len(embedding)}


async def _fae_write_embed(state: FetchAndEmbedState) -> FetchAndEmbedState:
    if not state.get("embedding"):
        return {**state, "embed_updated": False}
    try:
        from kotodama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        client.q(
            """
            UPDATE vertex_legal_corpus_document
               SET embedding_vec = %s,
                   embedding_dim = %s,
                   embedding_model = 'BAAI/bge-m3',
                   embedding_at = now()
             WHERE vertex_id = %s
            """,
            (state["embedding"], state["dim"], state["vertex_id"]),
        )
    except Exception as exc:
        return {**state, "embed_updated": False, "error": str(exc)}
    return {**state, "embed_updated": True}


def build_fetch_and_embed_graph() -> Any:
    g = StateGraph(FetchAndEmbedState)
    g.add_node("fetch_body",   _fae_fetch_body)
    g.add_node("write_body",   _fae_write_body)
    g.add_node("encode",       _fae_encode)
    g.add_node("write_embed",  _fae_write_embed)
    g.set_entry_point("fetch_body")
    g.add_edge("fetch_body",  "write_body")
    g.add_edge("write_body",  "encode")
    g.add_edge("encode",      "write_embed")
    g.add_edge("write_embed", END)
    return g.compile()


# ─────────────────────────────────────────────────────────────
# EUR-Lex body-text fetch helpers (shared with FetchAndEmbed)
# ─────────────────────────────────────────────────────────────

_UA = "Mozilla/5.0 (compatible; etzhayyim-legal-corpus/1.0; +https://legal-corpus.etzhayyim.com)"
_MAX_BODY_CHARS = 50_000


class _StripTags(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _fetch_eur_lex_xhtml(uri: str) -> tuple[int, str]:
    https_uri = uri.replace("http://", "https://", 1) if uri.startswith("http://") else uri
    req = urllib.request.Request(
        https_uri,
        headers={"Accept": "application/xhtml+xml", "Accept-Language": "en", "User-Agent": _UA},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read(_MAX_BODY_CHARS * 4)
            xhtml = raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return -1, f"transport: {e}"

    parser = _StripTags()
    parser.feed(xhtml)
    text = " ".join(parser.parts)
    text = re.sub(r"\s+", " ", text).strip()
    return 200, text[:_MAX_BODY_CHARS]


def _sparql_en_expr(work_uri: str) -> str | None:
    uuid = work_uri.rstrip("/").split("/")[-1]
    q = (
        "PREFIX cdm: <http://publications.europa.eu/ontology/cdm#> "
        "SELECT ?expr WHERE { "
        f"  <http://publications.europa.eu/resource/cellar/{uuid}> "
        "  cdm:is_realized_by ?expr . "
        "  ?expr cdm:expression_uses_language "
        "        <http://publications.europa.eu/resource/authority/language/ENG> . "
        "} LIMIT 1"
    )
    url = "https://publications.europa.eu/webapi/rdf/sparql?" + urllib.parse.urlencode(
        {"query": q, "format": "json"}
    )
    req = urllib.request.Request(
        url, headers={"Accept": "application/sparql-results+json", "User-Agent": _UA}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        bindings = data.get("results", {}).get("bindings", [])
        if bindings:
            expr_uri = bindings[0]["expr"]["value"]
            expr_uuid = expr_uri.rstrip("/").split("/")[-1].split(".")[0]
            return f"https://publications.europa.eu/resource/cellar/{expr_uuid}"
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────────
# Helper: build ingest input dict from a raw source item
# ─────────────────────────────────────────────────────────────

def _ingest_input(
    source_id: str,
    canonical_uri: str,
    document_type: str,
    title: str,
    language_code: str = "en",
    jurisdiction: str | None = None,
    court: str | None = None,
    court_did: str | None = None,
    citation: str | None = None,
    decided_at: str | None = None,
    published_at: str | None = None,
    body_text: str | None = None,
    body_uri: str | None = None,
    topic_tags: str | None = None,
    sensitivity_ord: int = 1,
) -> IngestState:
    return IngestState(
        source_id=source_id,
        canonical_uri=canonical_uri,
        document_type=document_type,
        jurisdiction=jurisdiction,
        court=court,
        court_did=court_did,
        language_code=language_code,
        title=title,
        citation=citation,
        decided_at=decided_at,
        published_at=published_at,
        fetched_at=_now(),
        body_text=body_text,
        body_uri=body_uri,
        topic_tags_csv=topic_tags,
        sensitivity_ord=sensitivity_ord,
        vertex_id="",
        already_known=False,
        error=None,
    )


# ─────────────────────────────────────────────────────────────
# 5. FetchEurLexDelta graph
#    Replaces: fetchEurLexDelta.bpmn (SPARQL → loop ingest)
# ─────────────────────────────────────────────────────────────

class FetchEurLexState(TypedDict):
    since_date:      str                              # ISO date, default 7 days ago
    items:           list[dict]
    ingest_results:  Annotated[list[dict], operator.add]
    error:           str | None


async def _eurlex_fetch(state: FetchEurLexState) -> FetchEurLexState:
    since = state.get("since_date") or (
        datetime.date.today() - datetime.timedelta(days=1)
    ).isoformat()
    sparql = (
        "PREFIX cdm: <http://publications.europa.eu/ontology/cdm#> "
        "SELECT DISTINCT ?work ?title ?date WHERE { "
        "  ?work cdm:work_has_resource-type ?rtype ; "
        "        cdm:work_date_document ?date . "
        "  ?expr cdm:expression_belongs_to_work ?work ; "
        "        cdm:expression_uses_language "
        "        <http://publications.europa.eu/resource/authority/language/ENG> ; "
        "        cdm:expression_title ?title . "
        "  VALUES ?rtype { "
        "    <http://publications.europa.eu/resource/authority/resource-type/DIR> "
        "    <http://publications.europa.eu/resource/authority/resource-type/REG> "
        "    <http://publications.europa.eu/resource/authority/resource-type/DEC_IMPL> "
        "  } "
        f'  FILTER(str(?date) >= "{since}") '
        "} ORDER BY DESC(?date) LIMIT 50"
    )
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://publications.europa.eu/webapi/rdf/sparql",
                content=sparql,
                headers={
                    "Content-Type": "application/sparql-query",
                    "Accept": "application/sparql-results+json",
                    "User-Agent": "etzhayyim-legal-corpus/1.0",
                },
            )
        bindings = r.json().get("results", {}).get("bindings", [])
    except Exception as exc:
        return {**state, "items": [], "error": str(exc)}
    items = [
        {
            "work": b["work"]["value"],
            "title": b.get("title", {}).get("value", ""),
            "date": b.get("date", {}).get("value", ""),
        }
        for b in bindings
    ]
    return {**state, "items": items, "error": None}


def _eurlex_fanout(state: FetchEurLexState) -> list[Send] | list[str]:
    items = state.get("items") or []
    if not items:
        return [END]
    return [
        Send("ingest_one", _ingest_input(
            source_id="eur-lex",
            canonical_uri=item["work"],
            document_type="regulation",
            jurisdiction="EU",
            language_code="eng",
            title=item.get("title", ""),
            decided_at=item.get("date"),
            sensitivity_ord=3,
        ))
        for item in items
    ]


async def _eurlex_ingest_one(state: IngestState) -> dict:
    result = await _get_ingest_graph().ainvoke(state)
    return {"ingest_results": [{"vertexId": result["vertex_id"], "alreadyKnown": result["already_known"]}]}


def build_fetch_eurlex_graph() -> Any:
    g = StateGraph(FetchEurLexState)
    g.add_node("fetch",       _eurlex_fetch)
    g.add_node("ingest_one",  _eurlex_ingest_one)
    g.set_entry_point("fetch")
    g.add_conditional_edges("fetch", _eurlex_fanout, ["ingest_one", END])
    g.add_edge("ingest_one", END)
    return g.compile()


# ─────────────────────────────────────────────────────────────
# 6. FetchCourtListenerDelta graph
#    Replaces: fetchCourtListenerDelta.bpmn
# ─────────────────────────────────────────────────────────────

class FetchCourtListenerState(TypedDict):
    cursor:         str | None
    secret_ref:     str
    items:          list[dict]
    next_cursor:    str | None
    ingest_results: Annotated[list[dict], operator.add]
    error:          str | None


async def _cl_load_cursor(state: FetchCourtListenerState) -> FetchCourtListenerState:
    from kotodama.kotoba_datomic import get_kotoba_client
    client = get_kotoba_client()
    rows = client.q(
        "SELECT last_cursor, secret_ref FROM vertex_legal_corpus_source"
        " WHERE source_id = 'courtlistener' LIMIT 1"
    )
    row = rows[0] if rows else None
    cursor = row["last_cursor"] if row else None
    secret = row["secret_ref"] if row else ""
    return {**state, "cursor": cursor, "secret_ref": secret}


async def _cl_fetch(state: FetchCourtListenerState) -> FetchCourtListenerState:
    since = state.get("cursor") or "1970-01-01"
    url = (
        f"https://www.courtlistener.com/api/rest/v3/opinions/"
        f"?date_modified__gt={since}&order_by=date_modified&page_size=100"
    )
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, headers={"Authorization": f"Token {state['secret_ref']}"})
        data = r.json()
        items     = data.get("results", [])
        next_cur  = data.get("next")
    except Exception as exc:
        return {**state, "items": [], "next_cursor": None, "error": str(exc)}
    return {**state, "items": items, "next_cursor": next_cur, "error": None}


def _cl_fanout(state: FetchCourtListenerState) -> list[Send] | list[str]:
    items = state.get("items") or []
    if not items:
        return ["advance_cursor"]
    return [
        Send("ingest_one", _ingest_input(
            source_id="courtlistener",
            canonical_uri=item.get("absolute_url", ""),
            document_type="opinion",
            jurisdiction="USA",
            court=item.get("cluster", {}).get("docket", {}).get("court_id"),
            language_code="en",
            title=(item.get("cluster") or {}).get("case_name", ""),
            citation=(item.get("cluster") or {}).get("citation_string"),
            decided_at=item.get("date_filed"),
            published_at=item.get("date_modified"),
            body_text=item.get("plain_text"),
            sensitivity_ord=1,
        ))
        for item in items
    ]


async def _cl_ingest_one(state: IngestState) -> dict:
    result = await _get_ingest_graph().ainvoke(state)
    return {"ingest_results": [{"vertexId": result["vertex_id"]}]}


async def _cl_advance_cursor(state: FetchCourtListenerState) -> FetchCourtListenerState:
    now = _now()
    next_cur = state.get("next_cursor")
    if next_cur:
        try:
            from kotodama.kotoba_datomic import get_kotoba_client
            client = get_kotoba_client()
            client.q(
                "UPDATE vertex_legal_corpus_source"
                " SET last_cursor = %s, last_fetched_at = %s"
                " WHERE source_id = 'courtlistener'",
                (next_cur, now),
            )
        except Exception as exc:
            return {**state, "error": str(exc)}
    return state


def build_fetch_courtlistener_graph() -> Any:
    g = StateGraph(FetchCourtListenerState)
    g.add_node("load_cursor",    _cl_load_cursor)
    g.add_node("fetch",          _cl_fetch)
    g.add_node("ingest_one",     _cl_ingest_one)
    g.add_node("advance_cursor", _cl_advance_cursor)
    g.set_entry_point("load_cursor")
    g.add_edge("load_cursor", "fetch")
    g.add_conditional_edges("fetch", _cl_fanout, ["ingest_one", "advance_cursor"])
    g.add_edge("ingest_one",     "advance_cursor")
    g.add_edge("advance_cursor", END)
    return g.compile()


# ─────────────────────────────────────────────────────────────
# 7. FetchBailiiDelta graph
#    Replaces: fetchBailiiDelta.bpmn (Atom feed → parallel ingest)
# ─────────────────────────────────────────────────────────────

class FetchBailiiState(TypedDict):
    items:          list[dict]
    ingest_results: Annotated[list[dict], operator.add]
    error:          str | None


async def _bailii_fetch(state: FetchBailiiState) -> FetchBailiiState:
    """Scrape BAILII year-based case list pages for UKSC and IESC.

    BAILII does not expose an Atom or RSS feed. Instead each court has a
    year-indexed HTML page at /uk/cases/UKSC/{year}/ etc.
    Case links are href-matched and canonicalised to full BAILII URLs.
    """
    year = datetime.date.today().year
    court_pages = [
        (f"https://www.bailii.org/uk/cases/UKSC/{year}/",
         r'href="(/uk/cases/UKSC/\d{4}/[^"]+\.html)"'),
        (f"https://www.bailii.org/ew/cases/EWCA/Civ/{year}/",
         r'href="(/ew/cases/EWCA/Civ/\d{4}/[^"]+\.html)"'),
        (f"https://www.bailii.org/ie/cases/IESC/{year}/",
         r'href="(/ie/cases/IESC/\d{4}/[^"]+\.html)"'),
    ]
    seen: set[str] = set()
    items: list[dict] = []
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for list_url, pattern in court_pages:
                r = await client.get(list_url, headers={"User-Agent": _UA})
                if r.status_code != 200:
                    continue
                if "not a bot" in r.text.lower() or "challenge" in r.text[:500].lower():
                    return {**state, "items": [], "error": "BAILII blocked by bot challenge (Vultr IPs)"}
                for path in re.findall(pattern, r.text):
                    url = "https://www.bailii.org" + path
                    if url in seen:
                        continue
                    seen.add(url)
                    items.append({
                        "link": url,
                        "title": path.rsplit("/", 1)[-1].replace(".html", ""),
                        "published": None,
                    })
    except Exception as exc:
        return {**state, "items": [], "error": str(exc)}
    return {**state, "items": items, "error": None}


def _bailii_jurisdiction(link: str) -> str:
    if "/ie/" in link:
        return "IRL"
    return "GBR"


def _bailii_fanout(state: FetchBailiiState) -> list[Send] | list[str]:
    items = state.get("items") or []
    if not items:
        return [END]
    return [
        Send("ingest_one", _ingest_input(
            source_id="bailii",
            canonical_uri=item["link"],
            document_type="opinion",
            jurisdiction=_bailii_jurisdiction(item["link"]),
            language_code="en",
            title=item["title"],
            decided_at=item.get("published"),
            sensitivity_ord=1,
        ))
        for item in items
    ]


async def _bailii_ingest_one(state: IngestState) -> dict:
    result = await _get_ingest_graph().ainvoke(state)
    return {"ingest_results": [{"vertexId": result["vertex_id"]}]}


def build_fetch_bailii_graph() -> Any:
    g = StateGraph(FetchBailiiState)
    g.add_node("fetch",      _bailii_fetch)
    g.add_node("ingest_one", _bailii_ingest_one)
    g.set_entry_point("fetch")
    g.add_conditional_edges("fetch", _bailii_fanout, ["ingest_one", END])
    g.add_edge("ingest_one", END)
    return g.compile()


# ─────────────────────────────────────────────────────────────
# 8. FetchWorldLiiDelta graph
#    Replaces: fetchWorldLiiDelta.bpmn (OAI-PMH R/P7D → parallel ingest)
# ─────────────────────────────────────────────────────────────

class FetchWorldLiiState(TypedDict):
    from_date:      str           # ISO date, default 7 days ago
    items:          list[dict]
    ingest_results: Annotated[list[dict], operator.add]
    error:          str | None


async def _worldlii_fetch(state: FetchWorldLiiState) -> FetchWorldLiiState:
    from_date = state.get("from_date") or (
        datetime.date.today() - datetime.timedelta(days=7)
    ).isoformat()
    url = (
        "https://www.worldlii.org/cgi-bin/oai.pl"
        f"?verb=ListRecords&metadataPrefix=oai_dc&from={from_date}"
    )
    import xml.etree.ElementTree as ET
    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            r = await client.get(url, headers={"User-Agent": _UA})
        root = ET.fromstring(r.text)
        ns = {
            "oai": "http://www.openarchives.org/OAI/2.0/",
            "dc":  "http://purl.org/dc/elements/1.1/",
            "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
        }
        records = root.findall(".//oai:record", ns)
        items = []
        for rec in records:
            meta = rec.find(".//oai_dc:dc", ns)
            if meta is None:
                continue
            title_el    = meta.find("dc:title", ns)
            identifier  = meta.find("dc:identifier", ns)
            date_el     = meta.find("dc:date", ns)
            items.append({
                "title":     title_el.text or "" if title_el is not None else "",
                "link":      identifier.text or "" if identifier is not None else "",
                "published": date_el.text or "" if date_el is not None else "",
            })
    except Exception as exc:
        return {**state, "items": [], "error": str(exc)}
    return {**state, "items": items, "error": None}


def _worldlii_fanout(state: FetchWorldLiiState) -> list[Send] | list[str]:
    items = state.get("items") or []
    if not items:
        return [END]
    return [
        Send("ingest_one", _ingest_input(
            source_id="worldlii",
            canonical_uri=item["link"],
            document_type="opinion",
            language_code="en",
            title=item["title"],
            decided_at=item.get("published"),
            sensitivity_ord=1,
        ))
        for item in items
    ]


async def _worldlii_ingest_one(state: IngestState) -> dict:
    result = await _get_ingest_graph().ainvoke(state)
    return {"ingest_results": [{"vertexId": result["vertex_id"]}]}


def build_fetch_worldlii_graph() -> Any:
    g = StateGraph(FetchWorldLiiState)
    g.add_node("fetch",      _worldlii_fetch)
    g.add_node("ingest_one", _worldlii_ingest_one)
    g.set_entry_point("fetch")
    g.add_conditional_edges("fetch", _worldlii_fanout, ["ingest_one", END])
    g.add_edge("ingest_one", END)
    return g.compile()


# ─────────────────────────────────────────────────────────────
# 9. FetchCanLiiDelta graph
#    Replaces: fetchCanLiiDelta.bpmn (CanLII API R/PT24H → parallel ingest)
# ─────────────────────────────────────────────────────────────

class FetchCanLiiState(TypedDict):
    canlii_key:     str
    items:          list[dict]
    ingest_results: Annotated[list[dict], operator.add]
    error:          str | None


async def _canlii_load_key(state: FetchCanLiiState) -> FetchCanLiiState:
    from kotodama.kotoba_datomic import get_kotoba_client
    client = get_kotoba_client()
    rows = client.q(
        "SELECT secret_ref FROM vertex_legal_corpus_source"
        " WHERE source_id = 'canlii' LIMIT 1"
    )
    row = rows[0] if rows else None
    key = row["secret_ref"] if row else ""
    return {**state, "canlii_key": key}


async def _canlii_fetch(state: FetchCanLiiState) -> FetchCanLiiState:
    since = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    key   = state.get("canlii_key", "")
    url   = (
        f"https://api.canlii.org/v1/caseBrowse/en/csc-scc/"
        f"?api_key={key}&decisionDateBegin={since}"
    )
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url)
        items = r.json().get("cases", [])
    except Exception as exc:
        return {**state, "items": [], "error": str(exc)}
    return {**state, "items": items, "error": None}


def _canlii_fanout(state: FetchCanLiiState) -> list[Send] | list[str]:
    items = state.get("items") or []
    if not items:
        return [END]
    return [
        Send("ingest_one", _ingest_input(
            source_id="canlii",
            canonical_uri=(
                "https://www.canlii.org/en/"
                + item.get("databaseId", "")
                + "/"
                + (item.get("caseId") or {}).get("en", "")
            ),
            document_type="opinion",
            jurisdiction="CAN",
            court="Supreme Court of Canada",
            language_code=item.get("language", "en"),
            title=item.get("title", ""),
            citation=item.get("citation"),
            decided_at=item.get("decisionDate"),
            sensitivity_ord=1,
        ))
        for item in items
    ]


async def _canlii_ingest_one(state: IngestState) -> dict:
    result = await _get_ingest_graph().ainvoke(state)
    return {"ingest_results": [{"vertexId": result["vertex_id"]}]}


def build_fetch_canlii_graph() -> Any:
    g = StateGraph(FetchCanLiiState)
    g.add_node("load_key",   _canlii_load_key)
    g.add_node("fetch",      _canlii_fetch)
    g.add_node("ingest_one", _canlii_ingest_one)
    g.set_entry_point("load_key")
    g.add_edge("load_key", "fetch")
    g.add_conditional_edges("fetch", _canlii_fanout, ["ingest_one", END])
    g.add_edge("ingest_one", END)
    return g.compile()


# ─────────────────────────────────────────────────────────────
# Module-level compiled graphs (instantiated once per process)
# ─────────────────────────────────────────────────────────────

ingest_document_graph      = build_ingest_document_graph()
embed_document_graph       = build_embed_document_graph()
search_document_graph      = build_search_document_graph()
fetch_and_embed_graph      = build_fetch_and_embed_graph()
fetch_eurlex_graph         = build_fetch_eurlex_graph()
fetch_courtlistener_graph  = build_fetch_courtlistener_graph()
fetch_bailii_graph         = build_fetch_bailii_graph()
fetch_worldlii_graph       = build_fetch_worldlii_graph()
fetch_canlii_graph         = build_fetch_canlii_graph()


def _get_ingest_graph() -> Any:
    return ingest_document_graph
