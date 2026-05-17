from typing import TypedDict
from langgraph.graph import StateGraph, END

class LinenState(TypedDict):
    material_specs: dict
    compliance_check: bool
    approved: bool

def validate_materials(state: LinenState):
    # Check for antimicrobial properties
    state['compliance_check'] = 'antimicrobial' in state['material_specs'].get('features', [])
    return state

def check_certification(state: LinenState):
    state['approved'] = state['compliance_check']
    return state

graph = StateGraph(LinenState)
graph.add_node('validate', validate_materials)
graph.add_node('certify', check_certification)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
graph = graph.compile()