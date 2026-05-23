"""LangGraph state graph wiring.

The 6 nodes + decision routing implement the state machine described in
ADR-2605231300 §"Decision". Edges:

  start → analyze → select_teacher → generate → validate → train → evaluate → decide
  decide -[commit]→ commit_node → END
  decide -[retry, iter<max]→ analyze (loop)
  decide -[retry, iter≥max | abort]→ abort_node → END
"""

from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph

from .nodes.analyze import analyze
from .nodes.evaluate import evaluate
from .nodes.fetch_dataset import fetch_dataset
from .nodes.generate import generate_training_data
from .nodes.select_teacher import select_teacher
from .nodes.train import train_lora
from .nodes.validate import validate_training_data
from .state import DistillState


def _route_after_decide(state: DistillState) -> Literal["commit", "loop", "abort"]:
    decision = state.get("decision", "pending")
    iteration = state.get("iter", 0)
    max_iter = state.get("max_iter", 3)
    if decision == "commit":
        return "commit"
    if decision == "retry" and iteration < max_iter:
        return "loop"
    return "abort"


def _route_after_analyze(state: DistillState) -> Literal["hf", "teacher"]:
    """ADR-2605231300 §3a/§3b split: default to HF dataset path; fall back
    to on-fleet teacher generation if explicitly requested."""
    return "teacher" if state.get("source") == "teacher" else "hf"


def _commit_node(state: DistillState) -> DistillState:
    from .nodes.commit import commit_to_registry

    commit_to_registry(state)
    state["notes"].append(
        f"[commit] iter={state['iter']} LoRA adapter at {state['lora_path']} "
        f"score_history={state['score_history']}"
    )
    return state


def _abort_node(state: DistillState) -> DistillState:
    import shutil

    state["notes"].append(
        f"[abort] iter={state['iter']} decision={state.get('decision')} — "
        f"adapter discarded; score_history={state['score_history']}"
    )
    lora = state.get("lora_path")
    if lora and not state.get("dry_run"):
        try:
            shutil.rmtree(lora, ignore_errors=True)
            state["notes"].append(f"[abort] removed {lora}")
        except Exception as e:  # pragma: no cover
            state["notes"].append(f"[abort] cleanup failed: {e!r}")
    return state


def build_graph() -> StateGraph:
    g = StateGraph(DistillState)

    g.add_node("analyze", analyze)
    g.add_node("fetch_dataset", fetch_dataset)
    g.add_node("select_teacher", select_teacher)
    g.add_node("generate", generate_training_data)
    g.add_node("validate", validate_training_data)
    g.add_node("train", train_lora)
    g.add_node("evaluate", evaluate)
    g.add_node("commit", _commit_node)
    g.add_node("abort", _abort_node)

    g.add_edge(START, "analyze")
    g.add_conditional_edges(
        "analyze", _route_after_analyze,
        {
            "hf": "fetch_dataset",
            "teacher": "select_teacher",
        },
    )
    g.add_edge("fetch_dataset", "validate")
    g.add_edge("select_teacher", "generate")
    g.add_edge("generate", "validate")
    g.add_edge("validate", "train")
    g.add_edge("train", "evaluate")

    g.add_conditional_edges(
        "evaluate", _route_after_decide,
        {
            "commit": "commit",
            "loop": "analyze",
            "abort": "abort",
        },
    )
    g.add_edge("commit", END)
    g.add_edge("abort", END)

    return g


def compile_graph():
    return build_graph().compile()
