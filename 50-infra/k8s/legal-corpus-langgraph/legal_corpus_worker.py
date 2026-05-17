"""legal-corpus LangServer worker.

Replaces pyzeebe task handlers for legal-corpus.etzhayyim.com
(ADR-0049, ADR-2605080600).

Task types registered:
  legal.corpus.embedText           — bge-m3 encode text → {embedding, dim}
  legal.corpus.searchDocument      — embed + cosine search (inline vec literal)
  legal.corpus.fetchBodyText       — fetch body text from canonical URI
  legal.corpus.ingestDocument      — dedupe + INSERT vertex_legal_corpus_document
  legal.corpus.embedDocument       — load body_text + bge-m3 + UPDATE embedding_vec
  legal.corpus.fetchAndEmbed       — fetch body + write + embed + write
  legal.corpus.fetchEurLexDelta    — EUR-Lex SPARQL delta (manual invoke)
  legal.corpus.fetchCourtListenerDelta — CourtListener API delta (manual invoke)
  legal.corpus.fetchBailiiDelta    — BAILII Atom delta (manual invoke)
  legal.corpus.fetchWorldLiiDelta  — WorldLii OAI-PMH delta (manual invoke)
  legal.corpus.fetchCanLiiDelta    — CanLII API delta (manual invoke)

Deployment: K8s Deployment `legal-corpus-worker` in namespace `mitama-udf`.
CronJobs for periodic fetch are defined in cronjob-*.yaml (separate manifests).
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException

from legal_corpus_langgraph import (
    _embed_text,
    _fetch_eur_lex_xhtml,
    _sparql_en_expr,
    embed_document_graph,
    fetch_and_embed_graph,
    fetch_bailii_graph,
    fetch_canlii_graph,
    fetch_courtlistener_graph,
    fetch_eurlex_graph,
    fetch_worldlii_graph,
    ingest_document_graph,
    search_document_graph,
    _ingest_input,
)

PORT = int(os.environ.get("PORT", os.environ.get("HEALTH_PORT", "8080")))
AGENTGATEWAY_MCP_URL = os.environ.get(
    "AGENTGATEWAY_MCP_URL",
    "http://agentgateway-mcp.mitama-udf.svc.cluster.local:8080",
)


class LangServerWorker:
    """Minimal LangServer HTTP shim."""

    def __init__(self, *, name: str = "legal-corpus-worker") -> None:
        self.name = name
        self.handlers: dict[str, Any] = {}

    def task(self, *, task_type: str, **_: Any) -> Any:
        def decorator(fn: Any) -> Any:
            self.handlers[task_type] = fn
            return fn
        return decorator

    async def work(self) -> None:
        app = FastAPI(title=self.name, version="1.0.0")

        @app.get("/healthz")
        async def healthz() -> dict[str, Any]:
            return {
                "ok": True,
                "runtimeKind": "k8s-langserver",
                "agentGatewayMcpUrl": AGENTGATEWAY_MCP_URL,
                "tools": sorted(self.handlers),
            }

        @app.get("/tools")
        async def tools() -> dict[str, Any]:
            return {
                "tools": [{"name": n, "runtime": "langserver"} for n in sorted(self.handlers)]
            }

        async def _dispatch(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
            handler = self.handlers.get(name)
            if handler is None:
                raise HTTPException(status_code=404, detail=f"unknown tool: {name}")
            return await handler(**arguments)

        @app.post("/invoke")
        async def invoke(payload: dict[str, Any]) -> dict[str, Any]:
            name = str(payload.get("name") or payload.get("tool") or "")
            args = payload.get("arguments") or payload.get("input") or {}
            if not isinstance(args, dict):
                raise HTTPException(status_code=400, detail="arguments must be an object")
            return {"ok": True, "name": name, "result": await _dispatch(name, args)}

        @app.post("/runs")
        async def runs(payload: dict[str, Any]) -> dict[str, Any]:
            assistant_id = str(payload.get("assistant_id") or "")
            args = payload.get("input") or payload.get("arguments") or {}
            if not isinstance(args, dict):
                raise HTTPException(status_code=400, detail="input must be an object")
            return {
                "status": "completed",
                "assistant_id": assistant_id,
                "output": await _dispatch(assistant_id, args),
            }

        config = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="info")
        await uvicorn.Server(config).serve()


async def _async_main() -> None:
    worker = LangServerWorker(name="legal-corpus-worker")

    # ── legal.corpus.embedText ────────────────────────────────
    @worker.task(task_type="legal.corpus.embedText")
    async def embed_text(text: str = "", **_: Any) -> dict[str, Any]:
        if not text:
            return {"embedding": [], "dim": 0}
        embedding = await _embed_text(text)
        return {"embedding": embedding, "dim": len(embedding)}

    # ── legal.corpus.searchDocument ───────────────────────────
    @worker.task(task_type="legal.corpus.searchDocument")
    async def search_document(
        queryText: str = "",
        jurisdiction: str = "",
        documentType: str = "",
        languageCode: str = "",
        decidedAfter: str = "",
        decidedBefore: str = "",
        limit: int = 10,
        **_: Any,
    ) -> dict[str, Any]:
        result = await search_document_graph.ainvoke({
            "query_text":    queryText,
            "jurisdiction":  jurisdiction,
            "document_type": documentType,
            "language_code": languageCode,
            "decided_after": decidedAfter,
            "decided_before": decidedBefore,
            "limit":         limit,
            "hits":          [],
            "hit_count":     0,
            "error":         None,
        })
        return {"hits": result["hits"], "hitCount": result["hit_count"], "error": result.get("error")}

    # ── legal.corpus.fetchBodyText ────────────────────────────
    @worker.task(task_type="legal.corpus.fetchBodyText")
    async def fetch_body_text(
        canonicalUri: str = "",
        sourceId: str = "",
        maxChars: int = 50_000,
        **_: Any,
    ) -> dict[str, Any]:
        if not canonicalUri:
            return {"error": "canonicalUri required", "bodyText": ""}

        if sourceId == "eur-lex" or "publications.europa.eu" in canonicalUri:
            status, text = await asyncio.to_thread(_fetch_eur_lex_xhtml, canonicalUri)
            if status == 200 and text.strip():
                return {"bodyText": text[:maxChars], "chars": min(len(text), maxChars), "status": status}
            if status in (404, 406):
                en_uri = await asyncio.to_thread(_sparql_en_expr, canonicalUri)
                if en_uri and en_uri != canonicalUri:
                    status2, text2 = await asyncio.to_thread(_fetch_eur_lex_xhtml, en_uri)
                    if status2 == 200 and text2.strip():
                        return {
                            "bodyText": text2[:maxChars],
                            "chars": min(len(text2), maxChars),
                            "status": status2,
                            "resolvedUri": en_uri,
                        }
            return {"error": f"eur-lex fetch {status}", "bodyText": "", "status": status}

        return {"error": f"unsupported sourceId={sourceId!r}", "bodyText": ""}

    # ── legal.corpus.ingestDocument ───────────────────────────
    @worker.task(task_type="legal.corpus.ingestDocument")
    async def ingest_document(
        sourceId: str = "",
        canonicalUri: str = "",
        documentType: str = "",
        jurisdiction: str | None = None,
        court: str | None = None,
        courtDid: str | None = None,
        languageCode: str = "en",
        title: str = "",
        citation: str | None = None,
        decidedAt: str | None = None,
        publishedAt: str | None = None,
        bodyText: str | None = None,
        bodyUri: str | None = None,
        topicTags: str | None = None,
        sensitivityOrd: int = 1,
        **_: Any,
    ) -> dict[str, Any]:
        state = _ingest_input(
            source_id=sourceId,
            canonical_uri=canonicalUri,
            document_type=documentType,
            jurisdiction=jurisdiction,
            court=court,
            court_did=courtDid,
            language_code=languageCode,
            title=title,
            citation=citation,
            decided_at=decidedAt,
            published_at=publishedAt,
            body_text=bodyText,
            body_uri=bodyUri,
            topic_tags=topicTags,
            sensitivity_ord=sensitivityOrd,
        )
        result = await ingest_document_graph.ainvoke(state)
        return {
            "vertexId":    result["vertex_id"],
            "alreadyKnown": result["already_known"],
            "error":       result.get("error"),
        }

    # ── legal.corpus.embedDocument ────────────────────────────
    @worker.task(task_type="legal.corpus.embedDocument")
    async def embed_document(vertexId: str = "", **_: Any) -> dict[str, Any]:
        result = await embed_document_graph.ainvoke({
            "vertex_id": vertexId,
            "body_text": "",
            "embedding": [],
            "dim":       0,
            "updated":   False,
            "error":     None,
        })
        return {"updated": result["updated"], "dim": result["dim"], "error": result.get("error")}

    # ── legal.corpus.fetchAndEmbed ────────────────────────────
    @worker.task(task_type="legal.corpus.fetchAndEmbed")
    async def fetch_and_embed(
        vertexId: str = "",
        canonicalUri: str = "",
        sourceId: str = "",
        **_: Any,
    ) -> dict[str, Any]:
        result = await fetch_and_embed_graph.ainvoke({
            "vertex_id":    vertexId,
            "canonical_uri": canonicalUri,
            "source_id":    sourceId,
            "body_text":    "",
            "embedding":    [],
            "dim":          0,
            "body_updated": False,
            "embed_updated": False,
            "error":        None,
        })
        return {
            "bodyUpdated":  result["body_updated"],
            "embedUpdated": result["embed_updated"],
            "error":        result.get("error"),
        }

    # ── legal.corpus.fetchEurLexDelta ─────────────────────────
    @worker.task(task_type="legal.corpus.fetchEurLexDelta")
    async def fetch_eurlex_delta(sinceDate: str = "", **_: Any) -> dict[str, Any]:
        result = await fetch_eurlex_graph.ainvoke({
            "since_date": sinceDate,
            "items":      [],
            "ingest_results": [],
            "error":      None,
        })
        return {
            "count": len(result.get("ingest_results") or []),
            "error": result.get("error"),
        }

    # ── legal.corpus.fetchCourtListenerDelta ──────────────────
    @worker.task(task_type="legal.corpus.fetchCourtListenerDelta")
    async def fetch_courtlistener_delta(**_: Any) -> dict[str, Any]:
        result = await fetch_courtlistener_graph.ainvoke({
            "cursor":         None,
            "secret_ref":     "",
            "items":          [],
            "next_cursor":    None,
            "ingest_results": [],
            "error":          None,
        })
        return {
            "count": len(result.get("ingest_results") or []),
            "error": result.get("error"),
        }

    # ── legal.corpus.fetchBailiiDelta ─────────────────────────
    @worker.task(task_type="legal.corpus.fetchBailiiDelta")
    async def fetch_bailii_delta(**_: Any) -> dict[str, Any]:
        result = await fetch_bailii_graph.ainvoke({
            "items":          [],
            "ingest_results": [],
            "error":          None,
        })
        return {
            "count": len(result.get("ingest_results") or []),
            "error": result.get("error"),
        }

    # ── legal.corpus.fetchWorldLiiDelta ───────────────────────
    @worker.task(task_type="legal.corpus.fetchWorldLiiDelta")
    async def fetch_worldlii_delta(fromDate: str = "", **_: Any) -> dict[str, Any]:
        result = await fetch_worldlii_graph.ainvoke({
            "from_date":      fromDate,
            "items":          [],
            "ingest_results": [],
            "error":          None,
        })
        return {
            "count": len(result.get("ingest_results") or []),
            "error": result.get("error"),
        }

    # ── legal.corpus.fetchCanLiiDelta ─────────────────────────
    @worker.task(task_type="legal.corpus.fetchCanLiiDelta")
    async def fetch_canlii_delta(**_: Any) -> dict[str, Any]:
        result = await fetch_canlii_graph.ainvoke({
            "canlii_key":     "",
            "items":          [],
            "ingest_results": [],
            "error":          None,
        })
        return {
            "count": len(result.get("ingest_results") or []),
            "error": result.get("error"),
        }

    await worker.work()


def main() -> None:
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
