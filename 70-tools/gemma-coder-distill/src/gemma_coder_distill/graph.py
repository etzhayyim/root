"""LangGraph state machine: analyze → fetch → validate → train → evaluate → commit.

Mirrors baien-distill but specialised for the LangGraph-coding bench and the
gemma-3 architecture. Per ADR-2605250400 §3 acceptance criteria.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .nodes.analyze import analyze
from .nodes.commit import commit
from .nodes.evaluate import evaluate
from .nodes.fetch_dataset import fetch_dataset
from .nodes.train import train_lora
from .nodes.validate import validate
from .state import DistillState


def _gate(state: DistillState) -> str:
    return state.get("decision", "continue")


def build_graph():
    g = StateGraph(DistillState)
    g.add_node("analyze", analyze)
    g.add_node("fetch_dataset", fetch_dataset)
    g.add_node("validate", validate)
    g.add_node("train", train_lora)
    g.add_node("evaluate", evaluate)
    g.add_node("commit", commit)

    g.add_edge(START, "analyze")
    g.add_conditional_edges("analyze", _gate, {"continue": "fetch_dataset", "abort": END})
    g.add_conditional_edges("fetch_dataset", _gate, {"continue": "validate", "abort": END})
    g.add_conditional_edges("validate", _gate, {"continue": "train", "abort": END})
    g.add_conditional_edges("train", _gate, {"continue": "evaluate", "abort": END})
    g.add_conditional_edges("evaluate", _gate, {
        "commit": "commit", "continue": "commit", "abort": END,
    })
    g.add_edge("commit", END)
    return g.compile()
