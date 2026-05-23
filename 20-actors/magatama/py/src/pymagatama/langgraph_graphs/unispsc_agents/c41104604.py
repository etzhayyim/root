from typing import TypedDict
from langgraph.graph import StateGraph, END

class FurnaceState(TypedDict):
    temp_req: float
    has_safety_cert: bool
    is_compliant: bool

def validate_specs(state: FurnaceState):
    state['is_compliant'] = state['temp_req'] > 0 and state['has_safety_cert']
    return state

def route_procurement(state: FurnaceState):
    return "process" if state['is_compliant'] else "reject"

graph = StateGraph(FurnaceState)
graph.add_node("validate", validate_specs)
graph.add_conditional_edges("validate", route_procurement)
graph.add_edge("validate", END)
graph.set_entry_point("validate")
graph = graph.compile()
