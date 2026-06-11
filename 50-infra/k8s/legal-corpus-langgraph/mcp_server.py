#!/usr/bin/env python3
"""legal-corpus MCP server — JSON-RPC 2.0 over HTTP.

Exposes four MCP tools for AI agents:
  legalCorpus.document.search  — semantic vector search via LangServer worker
  legalCorpus.document.list    — metadata list/filter from Kotoba/Datomic
  legalCorpus.corpus.status    — aggregate stats + embedding coverage
  legalCorpus.source.list      — ingest source registry + watermarks

ADR-0049, ADR-2605080600
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.request import Request, urlopen

MCP_AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN", "")
_RW_URL = os.environ.get("RW_URL", "")
LANGSERVER_URL = os.environ.get(
    "LANGSERVER_URL",
    "http://legal-corpus-worker.mitama-udf.svc.cluster.local:8080",
).strip().rstrip("/")
LANGSERVER_TIMEOUT_SEC = int(os.environ.get("LANGSERVER_TIMEOUT_SEC", "60"))
PORT = int(os.environ.get("PORT", "8081"))


def _rw_dsn() -> str:
    url = _RW_URL
    if url.startswith("postgresql+asyncpg://"):
        url = "postgresql://" + url[len("postgresql+asyncpg://"):]
    return url


TOOLS: list[dict[str, Any]] = [
    {
        "name": "legalCorpus.document.search",
        "description": (
            "Semantic vector search across the global legal corpus using bge-m3 "
            "1024-dimensional multilingual embeddings. Returns the closest documents "
            "ranked by cosine similarity. Supports optional filters for jurisdiction "
            "(ISO country code or region), document type, language, and decided-at "
            "date range. queryText is required; all other parameters are optional."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["queryText"],
            "properties": {
                "queryText":     {"type": "string", "description": "Natural-language search query"},
                "jurisdiction":  {"type": "string", "description": "ISO-3166-1 alpha-2 or region code (e.g. EU, US, GB, CA)"},
                "documentType":  {"type": "string", "description": "Document type filter (e.g. regulation, judgment, directive)"},
                "languageCode":  {"type": "string", "description": "BCP-47 language code (e.g. en, fr, de)"},
                "decidedAfter":  {"type": "string", "description": "ISO 8601 date lower bound (e.g. 2020-01-01)"},
                "decidedBefore": {"type": "string", "description": "ISO 8601 date upper bound"},
                "limit":         {"type": "integer", "description": "Maximum results to return (default 10, max 50)"},
            },
        },
    },
    {
        "name": "legalCorpus.document.list",
        "description": (
            "List legal corpus documents with metadata. Supports filtering by "
            "jurisdiction, source, document type, and embedding status. "
            "Returns title, canonical URI, source, jurisdiction, decided-at, and "
            "embedding availability for each document."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "jurisdiction": {"type": "string"},
                "sourceId":     {"type": "string", "description": "e.g. eur-lex, courtlistener, bailii, worldlii, canlii"},
                "documentType": {"type": "string"},
                "embeddedOnly": {"type": "boolean", "description": "Return only documents that have an embedding vector"},
                "limit":        {"type": "integer"},
                "dryRun":       {"type": "boolean"},
            },
        },
    },
    {
        "name": "legalCorpus.corpus.status",
        "description": (
            "Get legal corpus aggregate statistics: total document count, embedding "
            "coverage percentage, per-source counts, and per-jurisdiction counts."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "dryRun": {"type": "boolean"},
            },
        },
    },
    {
        "name": "legalCorpus.source.list",
        "description": (
            "List registered legal corpus ingest sources with their document counts, "
            "last fetched timestamps, and ingest watermarks."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "dryRun": {"type": "boolean"},
            },
        },
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def text_result(value: Any, *, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False, indent=2)}],
        "isError": is_error,
    }


def rw_rows(sql: str, args: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    dsn = _rw_dsn()
    if not dsn:
        raise RuntimeError("RW_URL is not configured")
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return list(cur.fetchall() or [])


def _call_langserver(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps({"name": name, "arguments": arguments}).encode("utf-8")
    req = Request(
        f"{LANGSERVER_URL}/invoke",
        data=payload,
        headers={"content-type": "application/json", "accept": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=LANGSERVER_TIMEOUT_SEC) as res:
        body = res.read()
    parsed = json.loads(body.decode("utf-8"))
    result = parsed.get("result") if isinstance(parsed, dict) else parsed
    if isinstance(result, dict):
        return result
    return {"raw": result}


def search_documents(args: dict[str, Any]) -> dict[str, Any]:
    query_text = str(args.get("queryText") or "").strip()
    if not query_text:
        return {"ok": False, "error": "queryText is required", "hits": [], "hitCount": 0}
    limit = args.get("limit") if isinstance(args.get("limit"), int) and args.get("limit") > 0 else 10
    limit = min(limit, 50)
    if not LANGSERVER_URL:
        return {"ok": False, "error": "LANGSERVER_URL is not configured", "hits": [], "hitCount": 0}
    try:
        result = _call_langserver("legal.corpus.searchDocument", {
            "queryText":     query_text,
            "jurisdiction":  str(args.get("jurisdiction") or ""),
            "documentType":  str(args.get("documentType") or ""),
            "languageCode":  str(args.get("languageCode") or ""),
            "decidedAfter":  str(args.get("decidedAfter") or ""),
            "decidedBefore": str(args.get("decidedBefore") or ""),
            "limit":         limit,
        })
        return {
            "ok":       True,
            "hits":     result.get("hits") or [],
            "hitCount": result.get("hitCount") or 0,
            "error":    result.get("error"),
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:300]}", "hits": [], "hitCount": 0}


def list_documents(args: dict[str, Any]) -> dict[str, Any]:
    limit = args.get("limit") if isinstance(args.get("limit"), int) and args.get("limit") > 0 else 50
    limit = min(limit, 500)
    filters: list[str] = []
    values: list[Any] = []
    if str(args.get("jurisdiction") or "").strip():
        values.append(str(args["jurisdiction"]).strip())
        filters.append("jurisdiction = %s")
    if str(args.get("sourceId") or "").strip():
        values.append(str(args["sourceId"]).strip())
        filters.append("source_id = %s")
    if str(args.get("documentType") or "").strip():
        values.append(str(args["documentType"]).strip())
        filters.append("document_type = %s")
    if args.get("embeddedOnly") is True:
        filters.append("embedding_vec IS NOT NULL")
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"""
        SELECT vertex_id, canonical_uri, source_id, document_type,
               jurisdiction, language_code, title, citation,
               decided_at, published_at,
               (embedding_vec IS NOT NULL) AS has_embedding,
               embedding_dim, embedding_model, created_at
          FROM vertex_legal_corpus_document
          {where}
         ORDER BY created_at DESC
         LIMIT {limit}
    """
    plan = {
        "table":   "vertex_legal_corpus_document",
        "sql":     " ".join(query.split()),
        "params":  values,
        "limit":   limit,
        "requires": ["RW_URL", "vertex_legal_corpus_document"],
    }
    if args.get("dryRun") is True or not _rw_dsn():
        return {
            "ok": True, "dryRun": True, "queryPlan": plan,
            "reason": "RW_URL is not configured" if not _rw_dsn() else "dryRun requested",
        }
    rows = rw_rows(query, tuple(values))
    return {"ok": True, "dryRun": False, "queryPlan": plan, "rows": rows, "rowCount": len(rows)}


def corpus_status(args: dict[str, Any]) -> dict[str, Any]:
    queries = {
        "total": "SELECT COUNT(*) AS n FROM vertex_legal_corpus_document",
        "embedded": "SELECT COUNT(*) AS n FROM vertex_legal_corpus_document WHERE embedding_vec IS NOT NULL",
        "by_source": """
            SELECT source_id, COUNT(*) AS n,
                   COUNT(CASE WHEN embedding_vec IS NOT NULL THEN 1 END) AS embedded
              FROM vertex_legal_corpus_document
             GROUP BY source_id
             ORDER BY n DESC
        """,
        "by_jurisdiction": """
            SELECT jurisdiction, COUNT(*) AS n
              FROM vertex_legal_corpus_document
             WHERE jurisdiction IS NOT NULL AND jurisdiction <> ''
             GROUP BY jurisdiction
             ORDER BY n DESC
             LIMIT 30
        """,
    }
    plan = {
        "queries": {k: " ".join(v.split()) for k, v in queries.items()},
        "requires": ["RW_URL", "vertex_legal_corpus_document"],
    }
    if args.get("dryRun") is True or not _rw_dsn():
        return {
            "ok": True, "dryRun": True, "queryPlan": plan,
            "reason": "RW_URL is not configured" if not _rw_dsn() else "dryRun requested",
        }
    total_rows = rw_rows(queries["total"])
    embedded_rows = rw_rows(queries["embedded"])
    by_source = rw_rows(queries["by_source"])
    by_jurisdiction = rw_rows(queries["by_jurisdiction"])
    total = int((total_rows[0] or {}).get("n") or 0)
    embedded = int((embedded_rows[0] or {}).get("n") or 0)
    coverage_pct = round(100.0 * embedded / total, 1) if total > 0 else 0.0
    return {
        "ok": True,
        "dryRun": False,
        "queryPlan": plan,
        "totalDocuments":    total,
        "embeddedDocuments": embedded,
        "coveragePct":       coverage_pct,
        "embeddingModel":    "BAAI/bge-m3",
        "embeddingDim":      1024,
        "bySource":          [dict(r) for r in by_source],
        "byJurisdiction":    [dict(r) for r in by_jurisdiction],
        "checkedAt":         utc_now(),
    }


def source_list(args: dict[str, Any]) -> dict[str, Any]:
    query = """
        SELECT s.source_id, s.display_name, s.jurisdiction, s.base_url,
               s.cursor_watermark, s.last_fetched_at, s.created_at,
               COUNT(d.vertex_id) AS document_count,
               COUNT(CASE WHEN d.embedding_vec IS NOT NULL THEN 1 END) AS embedded_count
          FROM vertex_legal_corpus_source s
          LEFT JOIN vertex_legal_corpus_document d ON d.source_id = s.source_id
         GROUP BY s.source_id, s.display_name, s.jurisdiction, s.base_url,
                  s.cursor_watermark, s.last_fetched_at, s.created_at
         ORDER BY s.source_id ASC
    """
    plan = {
        "sql":     " ".join(query.split()),
        "requires": ["RW_URL", "vertex_legal_corpus_source", "vertex_legal_corpus_document"],
    }
    if args.get("dryRun") is True or not _rw_dsn():
        return {
            "ok": True, "dryRun": True, "queryPlan": plan,
            "reason": "RW_URL is not configured" if not _rw_dsn() else "dryRun requested",
        }
    rows = rw_rows(query)
    return {"ok": True, "dryRun": False, "queryPlan": plan, "sources": [dict(r) for r in rows]}


def call_tool(name: str, args: dict[str, Any]) -> Any:
    if name == "legalCorpus.document.search":
        return search_documents(args)
    if name == "legalCorpus.document.list":
        return list_documents(args)
    if name == "legalCorpus.corpus.status":
        return corpus_status(args)
    if name == "legalCorpus.source.list":
        return source_list(args)
    raise ValueError(f"unknown tool: {name}")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self.write_json({"ok": True, "service": "legal-corpus-mcp", "time": utc_now()})
            return
        self.write_json({
            "ok":     True,
            "mcp":    "/mcp",
            "tools":  [t["name"] for t in TOOLS],
            "worker": LANGSERVER_URL,
        })

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.add_common_headers()
        self.end_headers()

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except Exception as exc:
            self.write_json(
                {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}, 400
            )
            return
        response = self.handle_rpc(payload)
        if response is None:
            self.write_json({}, 202)
        else:
            self.write_json(response)

    def handle_rpc(self, msg: dict[str, Any]) -> dict[str, Any] | None:
        rpc_id = msg.get("id")
        method = msg.get("method")
        if msg.get("jsonrpc") != "2.0" or not isinstance(method, str):
            return {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32600, "message": "malformed request"}}
        if rpc_id is None and "id" not in msg:
            return None
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "legal-corpus-mcp", "version": "0.1.0"},
                },
            }
        if method == "notifications/initialized":
            return None
        if method == "ping":
            return {"jsonrpc": "2.0", "id": rpc_id, "result": {}}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": TOOLS}}
        if method != "tools/call":
            return {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32601, "message": f"method not found: {method}"}}

        params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
        name = str(params.get("name") or "")
        args = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        if not name:
            return {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32602, "message": "params.name is required"}}
        if not self.authorized():
            return {"jsonrpc": "2.0", "id": rpc_id, "result": text_result({"ok": False, "error": "unauthorized"}, is_error=True)}
        try:
            return {"jsonrpc": "2.0", "id": rpc_id, "result": text_result(call_tool(name, args))}
        except Exception as exc:
            return {"jsonrpc": "2.0", "id": rpc_id, "result": text_result({"ok": False, "error": str(exc)}, is_error=True)}

    def authorized(self) -> bool:
        if not MCP_AUTH_TOKEN:
            return True
        return self.headers.get("Authorization") == f"Bearer {MCP_AUTH_TOKEN}"

    def add_common_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,Authorization,Mcp-Session-Id")

    def write_json(self, payload: Any, status: int = 200) -> None:
        body = json_dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.add_common_headers()
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[%s] %s\n" % (utc_now(), fmt % args))


def main() -> None:
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(json.dumps({
        "service": "legal-corpus-mcp",
        "port":    PORT,
        "tools":   [t["name"] for t in TOOLS],
        "worker":  LANGSERVER_URL,
    }), flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
