from typing import TypedDict
from langgraph.graph import StateGraph, END

class OfficeFurnitureState(TypedDict):
    specs: dict
    validation_status: str
    approval_required: bool

def validate_dimensions(state: OfficeFurnitureState):
    # Business logic for reception counter standard checks
    width = state['specs'].get('width', 0)
    state['validation_status'] = 'pass' if width > 0 else 'fail'
    return state

def check_compliance(state: OfficeFurnitureState):
    state['approval_required'] = state['specs'].get('fire_rated', False)
    return state

graph = StateGraph(OfficeFurnitureState)
graph.add_node('validate', validate_dimensions)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
