from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SensorState(TypedDict):
    specs: dict
    validated: bool
    compliance_check: bool

def validate_specs(state: SensorState):
    # Perform logic check for range and output compatibility
    state['validated'] = state['specs'].get('range_mm', 0) > 0
    return state

def check_compliance(state: SensorState):
    # Check for dual-use restrictions based on resolution
    state['compliance_check'] = state['specs'].get('resolution_um', 10) > 1
    return state

graph = StateGraph(SensorState)
graph.add_node("validate", validate_specs)
graph.add_node("compliance", check_compliance)
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph.set_entry_point("validate")
graph = graph.compile()
