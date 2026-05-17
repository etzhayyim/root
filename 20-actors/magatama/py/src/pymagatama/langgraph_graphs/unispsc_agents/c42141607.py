from typing import TypedDict
from langgraph.graph import StateGraph, END

class UrinalState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_sanitation(state: UrinalState):
    # Business logic for medical product compliance
    state['is_compliant'] = 'ISO_cert' in state['spec_data']
    return state

def check_material(state: UrinalState):
    # CAD or material validation logic
    return state

graph = StateGraph(UrinalState)
graph.add_node('validate', validate_sanitation)
graph.add_node('material_check', check_material)
graph.add_edge('validate', 'material_check')
graph.add_edge('material_check', END)
graph.set_entry_point('validate')
graph = graph.compile()