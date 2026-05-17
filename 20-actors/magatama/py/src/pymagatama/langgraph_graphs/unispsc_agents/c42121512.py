from typing import TypedDict
from langgraph.graph import StateGraph, END

class VetSpeculumState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_specifications(state: VetSpeculumState):
    errors = []
    if 'material' not in state['spec_data']: errors.append('Missing material spec')
    if 'sterilization_rating' not in state['spec_data']: errors.append('Missing sterilization rating')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def route_to_approval(state: VetSpeculumState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(VetSpeculumState)
graph.add_node('validate', validate_specifications)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()