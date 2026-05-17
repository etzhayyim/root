from typing import TypedDict
from langgraph.graph import StateGraph, END

class OrthoState(TypedDict):
    material_certified: bool
    fit_check_required: bool
    is_approved: bool

def validate_compliance(state: OrthoState):
    state['is_approved'] = state['material_certified'] and not state['fit_check_required']
    return state

graph = StateGraph(OrthoState)
graph.add_node('compliance', validate_compliance)
graph.set_entry_point('compliance')
graph.add_edge('compliance', END)
graph = graph.compile()