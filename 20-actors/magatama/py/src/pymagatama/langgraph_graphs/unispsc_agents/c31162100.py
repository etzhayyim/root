from typing import TypedDict
from langgraph.graph import StateGraph, END

class AnchorState(TypedDict):
    spec: dict
    validation_errors: list
    is_approved: bool

def validate_load_capacity(state: AnchorState):
    capacity = state['spec'].get('load_capacity', 0)
    if capacity <= 0:
        state['validation_errors'].append('Invalid load capacity')
    return {'is_approved': len(state['validation_errors']) == 0}

def structural_compliance_check(state: AnchorState):
    material = state['spec'].get('material', '')
    if not material:
        state['validation_errors'].append('Missing material specification')
    return {'is_approved': len(state['validation_errors']) == 0}

graph = StateGraph(AnchorState)
graph.add_node('validate_specs', validate_load_capacity)
graph.add_node('compliance_check', structural_compliance_check)
graph.set_entry_point('validate_specs')
graph.add_edge('validate_specs', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()
