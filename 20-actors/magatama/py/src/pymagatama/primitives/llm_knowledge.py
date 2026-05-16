"""LLM domain-knowledge retrieval and LangGraph answer primitives.

These functions are Zeebe worker task bodies for:
  - llm.knowledge.retrieve
  - llm.knowledge.langgraphAnswer

Facts are read from RisingWave domain-knowledge vertices/MVs. No domain facts
are hard-coded in Python or Cloudflare Workers.
"""

from __future__ import annotations

import os
import re
import time
from typing import Any, TypedDict

from pymagatama import llm
from pymagatama.db_sync import sync_cursor

try:
    from langgraph.graph import END, StateGraph
except Exception:  # pragma: no cover - optional in some worker images
    END = "__end__"
    StateGraph = None  # type: ignore[assignment]


class AnswerState(TypedDict, total=False):
    question: str
    contexts: list[dict[str, Any]]
    citations: list[str]
    tier: str
    lang: str
    ok: bool
    answer: str
    confidence: str
    model: str
    latencyMs: int
    error: str
    errorKind: str


# Keep the LLM attempt timeout below the BPMN result timeout. `llm.call_tier`
# retries once, so 40s + 2s backoff + 40s stays inside the 90s SSE result
# window and returns an explicit LlmError instead of silently hanging.
LLM_KNOWLEDGE_TIMEOUT_SEC = float(os.environ.get("LLM_KNOWLEDGE_TIMEOUT_SEC", "40"))


def _terms(question: str) -> list[str]:
    q = question.lower()
    raw = [x for x in re.split(r"[\s、。,.!?！？/]+", q) if len(x) >= 2]
    aliases = {
        "pokopia": ["ぽこあ", "ポコピア", "pokopia", "pokemon-pokopia"],
        "dream-island": ["夢島", "ゆめしま", "dream island"],
        "drifloon": ["フワンテ", "drifloon"],
        "habitat": ["棲家", "すみか", "あたたかい風"],
    }
    out = list(raw)
    for values in aliases.values():
        if any(v.lower() in q for v in values):
            out.extend(values)
    return list(dict.fromkeys(out))[:12]


def _fetch_citations(document_vids: list[str]) -> list[str]:
    if not document_vids:
        return []
    placeholders = ", ".join(["%s"] * len(document_vids))
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT s.url
            FROM edge_domain_knowledge_cites e
            JOIN vertex_domain_knowledge_source s ON s.vertex_id = e.dst_vid
            WHERE e.src_vid IN ({placeholders})
            ORDER BY s.confidence DESC, s.url ASC
            """,
            tuple(document_vids),
        )
        return list(dict.fromkeys(str(row[0]) for row in cur.fetchall()))


def retrieve(
    question: str,
    domain: str = "",
    gameSlug: str = "",
    lang: str = "ja",
    topK: int = 8,
) -> dict[str, Any]:
    qs = _terms(question)
    clauses = ["lang = %s"]
    params: list[Any] = [lang or "ja"]
    if domain:
        clauses.append("domain = %s")
        params.append(domain)
    if gameSlug:
        clauses.append("game_slug = %s")
        params.append(gameSlug)
    if qs:
        clauses.append("(" + " OR ".join(["search_text LIKE %s" for _ in qs]) + ")")
        params.extend([f"%{q.lower()}%" for q in qs])

    limit = max(1, min(int(topK or 8), 20))
    query = f"""
      SELECT chunk_vid, document_vid, domain, actor_did, canonical_work_id,
             game_slug, title, lang, chunk_index, chunk_text, keywords,
             confidence, updated_at
      FROM mv_domain_knowledge_search
      WHERE {" AND ".join(clauses)}
      ORDER BY updated_at DESC, chunk_index ASC
      LIMIT {limit}
    """
    with sync_cursor() as cur:
        cur.execute(query, tuple(params))
        colnames = [desc[0] for desc in cur.description]
        rows = [dict(zip(colnames, row)) for row in cur.fetchall()]

    used = sorted({str(row["document_vid"]) for row in rows})
    return {
        "contexts": rows,
        "citations": _fetch_citations(used),
        "usedKnowledge": used,
    }


def _answer_node(state: AnswerState) -> AnswerState:
    started = time.monotonic()
    contexts = state.get("contexts") or []
    citations = state.get("citations") or []
    if not contexts:
        return {
            **state,
            "ok": False,
            "answer": "該当する domain knowledge が RisingWave に見つかりませんでした。",
            "confidence": "low",
            "model": "none",
            "latencyMs": int((time.monotonic() - started) * 1000),
        }

    evidence = "\n\n".join(
        f"[{i + 1}] {c.get('title')}\n{c.get('chunk_text')}"
        for i, c in enumerate(contexts)
    )
    system = (
        "You answer only from provided evidence. If evidence is insufficient, say so. "
        "Return concise Japanese by default and include source URLs when present."
    )
    user = (
        f"Question:\n{state['question']}\n\n"
        f"Evidence:\n{evidence}\n\n"
        "Sources:\n" + "\n".join(f"- {c}" for c in citations)
    )
    try:
        result = llm.call_tier(
            state.get("tier") or "fast",
            system=system,
            user=user,
            max_tokens=900,
            temperature=0.1,
            timeout_sec=LLM_KNOWLEDGE_TIMEOUT_SEC,
        )
        answer = str(result.get("content") or "").strip()
        model = str(result.get("model") or "")
        latency = int(result.get("latencyMs") or int((time.monotonic() - started) * 1000))
    except llm.LlmError as exc:
        return {
            **state,
            "ok": False,
            "answer": "",
            "confidence": "error",
            "model": "",
            "latencyMs": int((time.monotonic() - started) * 1000),
            "error": f"llm backend failed: {exc}",
            "errorKind": type(exc).__name__,
        }
    if not answer:
        return {
            **state,
            "ok": False,
            "answer": "",
            "confidence": "error",
            "model": model,
            "latencyMs": latency,
            "error": "llm backend returned empty content",
            "errorKind": "EmptyLlmContent",
        }

    return {
        **state,
        "ok": True,
        "answer": answer,
        "confidence": "high" if len(contexts) >= 2 else "medium",
        "model": model,
        "latencyMs": latency,
    }


def _build_graph():
    if StateGraph is None:
        return None
    graph = StateGraph(AnswerState)
    graph.add_node("answer", _answer_node)
    graph.set_entry_point("answer")
    graph.add_edge("answer", END)
    return graph.compile()


_GRAPH = None


def answer(
    question: str,
    contexts: list[dict[str, Any]] | None = None,
    citations: list[str] | None = None,
    tier: str = "fast",
    lang: str = "ja",
) -> dict[str, Any]:
    global _GRAPH
    state: AnswerState = {
        "question": question,
        "contexts": contexts or [],
        "citations": citations or [],
        "tier": tier,
        "lang": lang,
    }
    if _GRAPH is None:
        _GRAPH = _build_graph()
    if _GRAPH is not None and hasattr(_GRAPH, "invoke"):
        result = _GRAPH.invoke(state)
    else:
        result = _answer_node(state)
    return {
        "ok": bool(result.get("ok", bool(result.get("answer")))),
        "answer": result.get("answer", ""),
        "confidence": result.get("confidence", "low"),
        "model": result.get("model", ""),
        "latencyMs": result.get("latencyMs", 0),
        "error": result.get("error", ""),
        "errorKind": result.get("errorKind", ""),
    }
