from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: PumpState):
    errors = []
    if state['spec_data'].get('power_rating', 0) <= 0:
        errors.append('Invalid power rating')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def route_by_validation(state: PumpState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(PumpState)
graph.add_node('validation', validate_specs)
graph.set_entry_point('validation')
graph.add_conditional_edges('validation', route_by_validation, {'approved': END, 'rejected': END})
graph.compile()