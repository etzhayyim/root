from typing import TypedDict
from langgraph.graph import StateGraph, END

class WagonProcurementState(TypedDict):
    load_capacity: float
    specs_verified: bool

def validate_specs(state: WagonProcurementState):
    state["specs_verified"] = state["load_capacity"] > 0
    return state

def route_procurement(state: WagonProcurementState):
    return "ready" if state["specs_verified"] else END

graph = StateGraph(WagonProcurementState)
graph.add_node("validate", validate_specs)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
app = graph.compile()