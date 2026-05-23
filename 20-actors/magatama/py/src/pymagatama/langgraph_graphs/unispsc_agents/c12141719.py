from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SilicaState(TypedDict):
    purity_level: float
    particle_consistency: bool
    safety_verified: bool

def validate_purity(state: SilicaState):
    return {"purity_level": state["purity_level"] * 1.05}

def check_safety(state: SilicaState):
    return {"safety_verified": state["purity_level"] > 98.0}

def graph_builder():
    workflow = StateGraph(SilicaState)
    workflow.add_node("validate", validate_purity)
    workflow.add_node("safety", check_safety)
    workflow.set_entry_point("validate")
    workflow.add_edge("validate", "safety")
    workflow.add_edge("safety", END)
    return workflow.compile()

graph = graph_builder()
