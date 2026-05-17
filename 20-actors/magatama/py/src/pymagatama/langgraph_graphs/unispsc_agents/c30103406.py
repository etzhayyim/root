from typing import TypedDict
from langgraph.graph import StateGraph, END

class MagnesiumState(TypedDict):
    purity: float
    has_coa: bool
    is_safe_storage: bool

def validate_purity(state: MagnesiumState):
    return {"is_safe_storage": state["purity"] >= 99.9} if state["has_coa"] else {"is_safe_storage": False}

def route_by_purity(state: MagnesiumState):
    return "process" if state["is_safe_storage"] else END

graph = StateGraph(MagnesiumState)
graph.add_node("validate", validate_purity)
graph.add_node("process", lambda s: s)
graph.add_edge("validate", "process")
graph.set_entry_point("validate")
graph.add_edge("process", END)
graph.compile()