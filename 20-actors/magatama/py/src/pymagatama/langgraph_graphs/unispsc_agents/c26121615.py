from typing import TypedDict
from langgraph.graph import StateGraph, END

class CableState(TypedDict):
    voltage: float
    burial_depth_mm: float
    compliance_code: str
    is_approved: bool

def validate_burial_specs(state: CableState):
    # Business logic for direct burial cable safety standards
    state['is_approved'] = state['burial_depth_mm'] >= 600 and state['voltage'] > 0
    return state

graph = StateGraph(CableState)
graph.add_node('validate', validate_burial_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()