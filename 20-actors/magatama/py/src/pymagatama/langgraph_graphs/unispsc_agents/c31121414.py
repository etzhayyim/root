from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_dimensions(state: CastingState):
    errors = []
    if state['spec_data'].get('tolerance', 0) > 0.05:
        errors.append('Tolerance exceeds precision threshold')
    return {'validation_errors': errors}

def approval_check(state: CastingState):
    is_approved = len(state['validation_errors']) == 0
    return {'is_approved': is_approved}

graph = StateGraph(CastingState)
graph.add_node('validate', validate_dimensions)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()