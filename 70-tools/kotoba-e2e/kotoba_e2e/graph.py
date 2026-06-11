"""LangGraph orchestration of the browser-only-kotoba e2e.

Flow (a StateGraph so steps are explicit + the LLM nodes degrade cleanly when
Murakumo is down):

    capture ─▶ assert_core ─▶ (murakumo up?) ─┬─ llm_judge ─▶ agent_explore ─▶ report
                                              └─ (skip) ─────────────────────▶ report

  * capture       — deterministic Playwright signal capture (browser.py)
  * assert_core   — pure pass/fail over signals (signals.py); sets browser_only_ok
  * llm_judge     — Murakumo LLM semantic judgement of the feed summary (gated)
  * agent_explore — browser-use Agent, Murakumo-driven exploration (gated)
  * report        — assemble the final verdict

The deterministic core (capture + assert_core + report) is what gates CI exit;
the LLM nodes add semantic confirmation when the fleet is available.
"""

from __future__ import annotations

import asyncio
from typing import Any, TypedDict

from . import agent as agent_mod
from . import browser as browser_mod
from . import signals as sig


class E2EState(TypedDict, total=False):
    url: str
    headless: bool
    use_agent: bool
    signals: Any
    checks: list
    browser_only_ok: bool
    murakumo_up: bool
    llm_verdict: str
    agent_verdict: dict
    report: dict


async def _capture(state: E2EState) -> E2EState:
    s = await browser_mod.capture_signals(state["url"], headless=state.get("headless", True))
    return {"signals": s}


def _assert_core(state: E2EState) -> E2EState:
    ok, checks = sig.evaluate(state["signals"])
    return {"browser_only_ok": ok, "checks": checks}


async def _llm_judge(state: E2EState) -> E2EState:
    s = state["signals"]
    summary = (
        f"Observed: {s.post_count} post cards rendered; "
        f"SW controller={s.sw_controller}; "
        f"requests to AppView host={sum(1 for r in s.requests if sig.APPVIEW_HOST in r.url)}; "
        f"kotoba block requests={sum(1 for r in s.requests if '/kotoba/blocks/' in r.url)}."
    )
    try:
        llm = agent_mod.murakumo.make_llm()
        prompt = (
            "You are a QA judge for a social web app. Given these observations, "
            "answer in one word PASS or FAIL, then a one-sentence reason. "
            "PASS means a working social feed rendered browser-side.\n\n" + summary
        )
        resp = await asyncio.to_thread(lambda: llm.invoke(prompt))
        verdict = getattr(resp, "content", None) or str(resp)
    except Exception as e:  # Murakumo hiccup — don't fail the run on the soft node
        verdict = f"(llm_judge skipped: {e})"
    return {"llm_verdict": str(verdict)}


async def _agent_explore(state: E2EState) -> E2EState:
    if not state.get("use_agent"):
        return {"agent_verdict": {"ran": False, "summary": "agent disabled (--no-agent)"}}
    try:
        v = await agent_mod.run_agent_task(state["url"])
    except Exception as e:
        v = {"ran": False, "summary": f"agent skipped: {e}"}
    return {"agent_verdict": v}


def _report(state: E2EState) -> E2EState:
    checks = state.get("checks", [])
    return {"report": {
        "url": state["url"],
        "browser_only_ok": state.get("browser_only_ok", False),
        "checks": [{"name": c.name, "passed": c.passed, "detail": c.detail} for c in checks],
        "murakumo_up": state.get("murakumo_up", False),
        "llm_verdict": state.get("llm_verdict"),
        "agent_verdict": state.get("agent_verdict"),
    }}


async def _probe_murakumo(state: E2EState) -> E2EState:
    return {"murakumo_up": await agent_mod.murakumo_reachable()}


def _after_assert(state: E2EState) -> str:
    return "llm_judge" if state.get("murakumo_up") else "report"


def build_graph():
    """Compile the StateGraph. Falls back to a plain async pipeline if langgraph
    is not installed (same node order), so the harness runs either way."""
    try:
        from langgraph.graph import END, StateGraph
    except Exception:
        return None  # caller uses run_pipeline()

    g = StateGraph(E2EState)
    g.add_node("capture", _capture)
    g.add_node("probe_murakumo", _probe_murakumo)
    g.add_node("assert_core", _assert_core)
    g.add_node("llm_judge", _llm_judge)
    g.add_node("agent_explore", _agent_explore)
    g.add_node("report", _report)
    g.set_entry_point("capture")
    g.add_edge("capture", "probe_murakumo")
    g.add_edge("probe_murakumo", "assert_core")
    g.add_conditional_edges("assert_core", _after_assert, {"llm_judge": "llm_judge", "report": "report"})
    g.add_edge("llm_judge", "agent_explore")
    g.add_edge("agent_explore", "report")
    g.add_edge("report", END)
    return g.compile()


async def run_pipeline(url: str, *, headless: bool = True, use_agent: bool = True) -> dict:
    """Run the e2e. Uses the compiled LangGraph when available, else an inline
    pipeline with identical node order."""
    state: E2EState = {"url": url, "headless": headless, "use_agent": use_agent}
    app = build_graph()
    if app is not None:
        out = await app.ainvoke(state)
        return out["report"]
    # Inline fallback (no langgraph): same order.
    state.update(await _capture(state))
    state.update(await _probe_murakumo(state))
    state.update(_assert_core(state))
    if state.get("murakumo_up"):
        state.update(await _llm_judge(state))
        state.update(await _agent_explore(state))
    state.update(_report(state))
    return state["report"]
