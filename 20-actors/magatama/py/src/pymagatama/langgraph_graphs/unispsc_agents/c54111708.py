from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PendulumState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_physical_specs(state: PendulumState):
    errors = []
    if state['spec_data'].get('weight_tolerance', 0) > 0.05:
        errors.append('Weight tolerance exceeds allowable limit.')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def update_workflow(state: PendulumState):
    return {'status': 'processed' if state['is_approved'] else 'rejected'}

builder = StateGraph(PendulumState)
builder.add_node('validate', validate_physical_specs)
builder.add_node('finalize', update_workflow)
builder.add_edge('validate', 'finalize')
builder.add_edge('finalize', END)
builder.set_entry_point('validate')
graph = builder.compile()