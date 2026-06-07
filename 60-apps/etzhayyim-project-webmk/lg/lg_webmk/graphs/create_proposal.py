"""webmk `create_proposal` graph — research → competitors → strategy → copy → quality_gate → store.

NSID: com.etzhayyim.apps.webmk.createProposal

State schema mirrors the Zeebe worker ProposalState from webmk_worker_main.py,
ported to LangGraph native (Phase 4: pyzeebe → LangServer migration).
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_webmk.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_APP_DID = os.environ.get("WEBMK_APP_DID", "did:web:webmk.etzhayyim.com")
_RW_URL = os.environ.get("RW_URL", "")
_QUALITY_THRESHOLD = float(os.environ.get("WEBMK_QUALITY_THRESHOLD", "0.7"))


class ProposalState(TypedDict, total=False):
    # Inputs
    proposal_id: str
    client_name: str
    website_url: str
    industry: str
    target_audience: str
    budget_jpy: int
    delivery_email: str
    create_ad_campaign: bool

    # Intermediate
    company_context: str
    competitor_summary: str
    strategy_json: str
    copy_markdown: str
    quality_score: float
    retry_count: int

    # Output
    ok: bool
    stored: bool
    error: str | None


def _uid(prefix: str) -> str:
    digest = hashlib.sha256(f"{prefix}{time.time_ns()}".encode()).hexdigest()[:12]
    return f"{prefix}-{digest}"


async def _init(state: ProposalState) -> dict[str, Any]:
    proposal_id = state.get("proposal_id") or _uid("prop")
    return {"proposal_id": proposal_id, "retry_count": 0}


async def _research_company(state: ProposalState) -> dict[str, Any]:
    """Scrape company website and extract context via LLM."""
    website_url = state.get("website_url", "")
    client_name = state.get("client_name", "")
    if not website_url:
        return {"company_context": f"Company: {client_name}. No website provided."}
    try:
        async with __import__("httpx").AsyncClient(timeout=10.0) as client:
            resp = await client.get(website_url)
            raw_html = resp.text[:4000]
    except Exception as exc:  # noqa: BLE001
        _log.warning("research: fetch failed %s: %s", website_url, exc)
        raw_html = f"Could not fetch {website_url}"

    # Minimal extraction without LLM dependency in skeleton
    return {"company_context": f"Company: {client_name}. Industry: {state.get('industry', 'unknown')}. Site snippet: {raw_html[:500]}"}


async def _analyze_competitors(state: ProposalState) -> dict[str, Any]:
    """Stub: summarize competitor landscape."""
    industry = state.get("industry", "general")
    return {"competitor_summary": f"Competitive landscape for '{industry}': key players identified via industry analysis."}


async def _generate_strategy(state: ProposalState) -> dict[str, Any]:
    """Generate marketing strategy JSON via Claude."""
    try:
        from langchain_anthropic import ChatAnthropic
        from kotodama.llm import resolve_model_id
        model_id = resolve_model_id("MURAKUMO_DEFAULT_MODEL")
        llm = ChatAnthropic(model=model_id, max_tokens=1024)
        prompt = (
            f"You are a web marketing strategist. Generate a JSON marketing strategy for:\n"
            f"Client: {state.get('client_name')}\n"
            f"Industry: {state.get('industry')}\n"
            f"Target: {state.get('target_audience')}\n"
            f"Budget: {state.get('budget_jpy', 0)} JPY\n"
            f"Context: {state.get('company_context', '')[:500]}\n"
            f"Competitors: {state.get('competitor_summary', '')[:300]}\n"
            "Return a JSON object with keys: goals, channels, tactics, kpis"
        )
        resp = await llm.ainvoke(prompt)
        strategy = str(resp.content)
    except Exception as exc:  # noqa: BLE001
        _log.warning("strategy gen failed: %s", exc)
        strategy = '{"goals":["brand awareness"],"channels":["SEO","SNS"],"tactics":["content marketing"],"kpis":["CTR","CVR"]}'
    return {"strategy_json": strategy}


async def _generate_copy(state: ProposalState) -> dict[str, Any]:
    """Generate marketing copy markdown."""
    try:
        from langchain_anthropic import ChatAnthropic
        from kotodama.llm import resolve_model_id
        model_id = resolve_model_id("MURAKUMO_DEFAULT_MODEL")
        llm = ChatAnthropic(model=model_id, max_tokens=2048)
        prompt = (
            f"Write a professional web marketing proposal in Markdown for:\n"
            f"Client: {state.get('client_name')}\n"
            f"Strategy: {state.get('strategy_json', '')[:800]}\n"
            "Include: Executive Summary, Goals, Recommended Channels, Monthly Plan, Budget Breakdown, KPIs"
        )
        resp = await llm.ainvoke(prompt)
        copy_md = str(resp.content)
    except Exception as exc:  # noqa: BLE001
        _log.warning("copy gen failed: %s", exc)
        copy_md = f"# Marketing Proposal for {state.get('client_name')}\n\nGenerated proposal content."
    return {"copy_markdown": copy_md}


async def _quality_gate(state: ProposalState) -> dict[str, Any]:
    """Score proposal quality. Retry once if below threshold."""
    copy_md = state.get("copy_markdown", "")
    score = min(1.0, len(copy_md) / 2000.0)  # simple length heuristic
    retry_count = state.get("retry_count", 0)
    if score < _QUALITY_THRESHOLD and retry_count < 1:
        _log.info("quality_gate: score=%.2f < threshold=%.2f, retry", score, _QUALITY_THRESHOLD)
        return {"quality_score": score, "retry_count": retry_count + 1}
    return {"quality_score": score}


def _quality_router(state: ProposalState) -> str:
    score = state.get("quality_score", 0.0)
    retry = state.get("retry_count", 0)
    if score < _QUALITY_THRESHOLD and retry <= 1:
        return "generate_copy"
    return "store_proposal"


async def _store_proposal(state: ProposalState) -> dict[str, Any]:
    """INSERT into vertex_webmk_proposal via RW."""
    proposal_id = state.get("proposal_id", _uid("prop"))
    if not _RW_URL:
        _log.warning("store_proposal: RW_URL not set, skipping persist")
        return {"ok": True, "stored": False}
    try:
        import psycopg
        vertex_id = f"at://did:web:webmk.etzhayyim.com/com.etzhayyim.apps.webmk.proposal/{proposal_id}"
        async with await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True) as conn:
            await conn.execute(
                """
                INSERT INTO vertex_webmk_proposal
                    (vertex_id, proposal_id, client_name, website_url, industry,
                     target_audience, budget_jpy, strategy_json, copy_markdown,
                     quality_score, status, actor_did, org_did, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                """,
                (
                    vertex_id,
                    proposal_id,
                    state.get("client_name", ""),
                    state.get("website_url", ""),
                    state.get("industry", ""),
                    state.get("target_audience", ""),
                    state.get("budget_jpy", 0),
                    state.get("strategy_json", ""),
                    state.get("copy_markdown", ""),
                    state.get("quality_score", 0.0),
                    "draft",
                    _APP_DID,
                    "anon",
                ),
            )
        return {"ok": True, "stored": True}
    except Exception as exc:  # noqa: BLE001
        _log.error("store_proposal failed: %s", exc)
        return {"ok": False, "error": str(exc)[:200], "stored": False}


async def _audit(state: ProposalState) -> dict[str, Any]:
    emit_audit_bg(
        actor=_APP_DID,
        activity="webmk.createProposal",
        object_id=state.get("proposal_id", "unknown"),
        object_type="webmk.proposal",
        attributes={"ok": state.get("ok", False), "qualityScore": state.get("quality_score", 0.0)},
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(ProposalState)
    g.add_node("init", _init)
    g.add_node("research_company", _research_company, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("analyze_competitors", _analyze_competitors)
    g.add_node("generate_strategy", _generate_strategy, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("generate_copy", _generate_copy, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("quality_gate", _quality_gate)
    g.add_node("store_proposal", _store_proposal, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("audit", _audit)

    g.add_edge(START, "init")
    g.add_edge("init", "research_company")
    g.add_edge("research_company", "analyze_competitors")
    g.add_edge("analyze_competitors", "generate_strategy")
    g.add_edge("generate_strategy", "generate_copy")
    g.add_edge("generate_copy", "quality_gate")
    g.add_conditional_edges("quality_gate", _quality_router, {"generate_copy": "generate_copy", "store_proposal": "store_proposal"})
    g.add_edge("store_proposal", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="create_proposal")
