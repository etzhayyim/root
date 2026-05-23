from typing import TypedDict
from langgraph.graph import StateGraph, END

class DepalletizerState(TypedDict):
    capacity: float
    safety_compliant: bool
    vendor_validated: bool

def validate_capacity(state: DepalletizerState):
    return {'vendor_validated': state['capacity'] > 0}

def check_compliance(state: DepalletizerState):
    return {'safety_compliant': True}

graph = StateGraph(DepalletizerState)
graph.add_node('validate_spec', validate_capacity)
graph.add_node('check_safety', check_compliance)
graph.set_entry_point('validate_spec')
graph.add_edge('validate_spec', 'check_safety')
graph.add_edge('check_safety', END)
graph = graph.compile()
