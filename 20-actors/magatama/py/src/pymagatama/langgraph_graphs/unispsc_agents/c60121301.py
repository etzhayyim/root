from typing import TypedDict
from langgraph.graph import StateGraph, END

class TrimmerState(TypedDict):
    model_number: str
    blade_safety_certified: bool
    max_pages: int

def validate_safety(state: TrimmerState):
    return {"blade_safety_certified": state.get("blade_safety_certified", False)}

def audit_spec(state: TrimmerState):
    return {"status": "verified" if state["max_pages"] > 0 else "error"}

graph = StateGraph(TrimmerState)
graph.add_node("validate", validate_safety)
graph.add_node("audit", audit_spec)
graph.set_entry_point("validate")
graph.add_edge("validate", "audit")
graph.add_edge("audit", END)
graph = graph.compile()