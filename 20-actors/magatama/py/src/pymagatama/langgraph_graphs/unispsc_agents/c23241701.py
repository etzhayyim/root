from typing import TypedDict
from langgraph.graph import StateGraph, END

class ShotBlastState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_tech_specs(state: ShotBlastState):
    errors = []
    if 'noise_db' not in state['spec_data'] or state['spec_data']['noise_db'] > 85:
        errors.append('Noise level exceeds safety limits')
    return {'validation_errors': errors}

def approval_check(state: ShotBlastState):
    return {'is_approved': len(state['validation_errors']) == 0}

graph = StateGraph(ShotBlastState)
graph.add_node('validate', validate_tech_specs)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
