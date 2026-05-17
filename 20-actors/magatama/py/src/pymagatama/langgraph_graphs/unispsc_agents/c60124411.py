from typing import TypedDict
from langgraph.graph import StateGraph, END

class WireState(TypedDict):
    gauge: float
    alloy_certified: bool
    passed_inspection: bool

def validate_specs(state: WireState):
    # Business logic for wire procurement validation
    is_valid = state['alloy_certified'] and state['gauge'] > 0
    return {"passed_inspection": is_valid}

def route_by_spec(state: WireState):
    return "process" if state['passed_inspection'] else END

graph = StateGraph(WireState)
graph.add_node("process", validate_specs)
graph.set_entry_point("process")
graph.add_edge("process", END)
graph = graph.compile()