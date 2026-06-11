"""Intake matching StateGraph.

triage → summarize → search → match → END
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from lg_lawfirm_intake.nodes import match_node, search_node, summarize_node, triage_node  # type: ignore[import-untyped]
from lg_lawfirm_intake.state import IntakeState  # type: ignore[import-untyped]


def build_graph():
    g = StateGraph(IntakeState)

    g.add_node("triage", triage_node)
    g.add_node("summarize", summarize_node)
    g.add_node("search", search_node)
    g.add_node("match", match_node)

    g.add_edge(START, "triage")
    g.add_edge("triage", "summarize")
    g.add_edge("summarize", "search")
    g.add_edge("search", "match")
    g.add_edge("match", END)

    return g.compile(name="lawfirm_intake")
