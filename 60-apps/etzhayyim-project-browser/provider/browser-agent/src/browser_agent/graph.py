"""LangGraph browser search graph — Genspark-like Sparkpage synthesis."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .nodes import plan_queries, quality_check, scrape_pages, search_web, synthesize
from .state import BrowserSearchState


def _route_after_quality(state: BrowserSearchState) -> str:
    return "plan_queries" if state.needs_more else END


def build_graph() -> StateGraph:
    g = StateGraph(BrowserSearchState)

    g.add_node("plan_queries", plan_queries)
    g.add_node("search_web", search_web)
    g.add_node("scrape_pages", scrape_pages)
    g.add_node("synthesize", synthesize)
    g.add_node("quality_check", quality_check)

    g.add_edge(START, "plan_queries")
    g.add_edge("plan_queries", "search_web")
    g.add_edge("search_web", "scrape_pages")
    g.add_edge("scrape_pages", "synthesize")
    g.add_edge("synthesize", "quality_check")
    g.add_conditional_edges("quality_check", _route_after_quality, ["plan_queries", END])

    return g


browser_search_graph = build_graph().compile()
