from typing import TypedDict
from langgraph.graph import StateGraph, END

class SterilizationState(TypedDict):
    material_type: str
    is_compliant: bool

def validate_materials(state: SterilizationState):
    state['is_compliant'] = state['material_type'] in ['non-woven', 'medical-grade-paper']
    return state

def approval_check(state: SterilizationState):
    return 'approved' if state['is_compliant'] else 'rejected'

graph = StateGraph(SterilizationState)
graph.add_node('validation', validate_materials)
graph.add_edge('validation', END)
graph.set_entry_point('validation')
graph = graph.compile()
