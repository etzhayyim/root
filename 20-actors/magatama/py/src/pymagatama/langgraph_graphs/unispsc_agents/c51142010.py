from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    has_msds: bool
    is_verified: bool

def validate_purity(state: ChemicalState):
    return {"is_verified": state["purity"] >= 0.99}

def safety_check(state: ChemicalState):
    return {"is_verified": state["has_msds"] and state["is_verified"]}

graph = StateGraph(ChemicalState)
graph.add_node("validate", validate_purity)
graph.add_node("safety", safety_check)
graph.set_entry_point("validate")
graph.add_edge("validate", "safety")
graph.add_edge("safety", END)
graph = graph.compile()
