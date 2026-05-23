from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastPartState(TypedDict):
    material_type: str
    purity_grade: float
    inspection_passed: bool

def validate_lead_purity(state: CastPartState):
    return {"inspection_passed": state["purity_grade"] >= 99.9}

def check_dimensions(state: CastPartState):
    return {"inspection_passed": True}

graph = StateGraph(CastPartState)
graph.add_node("validate_purity", validate_lead_purity)
graph.add_node("dimension_check", check_dimensions)
graph.set_entry_point("validate_purity")
graph.add_edge("validate_purity", "dimension_check")
graph.add_edge("dimension_check", END)
graph = graph.compile()
