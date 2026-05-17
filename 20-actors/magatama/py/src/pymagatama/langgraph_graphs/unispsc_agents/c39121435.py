from typing import TypedDict
from langgraph.graph import StateGraph, END

class WireProcessingState(TypedDict):
    wire_gauge: float
    voltage_rating: float
    compliant: bool

def validate_wire_specs(state: WireProcessingState):
    state["compliant"] = state["wire_gauge"] > 0 and state["voltage_rating"] >= 12
    return state

def check_compliance(state: WireProcessingState):
    return "compliant" if state["compliant"] else "non_compliant"

graph = StateGraph(WireProcessingState)
graph.add_node("validate", validate_wire_specs)
graph.add_edge("validate", END)
graph.set_entry_point("validate")
graph = graph.compile()