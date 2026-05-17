from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FluxState(TypedDict):
    material_data: dict
    validation_errors: List[str]
    approved: bool

def validate_chemical_specs(state: FluxState):
    errors = []
    if 'flash_point' not in state['material_data']:
        errors.append('Missing Flash Point data')
    return {'validation_errors': errors}

def approval_node(state: FluxState):
    is_approved = len(state['validation_errors']) == 0
    return {'approved': is_approved}

graph = StateGraph(FluxState)
graph.add_node('validate', validate_chemical_specs)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()