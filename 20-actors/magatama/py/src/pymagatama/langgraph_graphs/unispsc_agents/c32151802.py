from typing import TypedDict
from langgraph.graph import StateGraph, END

class SafetyModuleState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_safety_compliance(state: SafetyModuleState):
    # Simulate regulatory validation logic
    sil_level = state['spec_data'].get('sil', 0)
    state['is_compliant'] = sil_level >= 3
    return state

def route_procurement(state: SafetyModuleState):
    return 'approve' if state['is_compliant'] else 'reject'

graph = StateGraph(SafetyModuleState)
graph.add_node('validate', validate_safety_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

graph = graph.compile()
