from typing import TypedDict
from langgraph.graph import StateGraph, END

class BakeryState(TypedDict):
    temp_log: float
    has_allergen_label: bool
    is_expired: bool

def validate_temp(state: BakeryState):
    return {"is_compliant": state["temp_log"] <= 5.0}

def check_quality(state: BakeryState):
    return {"status": "APPROVED" if not state["is_expired"] and state["has_allergen_label"] else "REJECTED"}

graph = StateGraph(BakeryState)
graph.add_node("validate_temp", validate_temp)
graph.add_node("check_quality", check_quality)
graph.add_edge("validate_temp", "check_quality")
graph.add_edge("check_quality", END)
graph.set_entry_point("validate_temp")
graph = graph.compile()
