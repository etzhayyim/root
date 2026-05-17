from typing import TypedDict
from langgraph.graph import StateGraph, END

class RubberBeamState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_physical_specs(state: RubberBeamState):
    errors = []
    if state['spec_data'].get('durometer', 0) < 50:
        errors.append('Insufficient hardness for structural load.')
    return {'validation_errors': errors}

def check_compliance(state: RubberBeamState):
    status = len(state['validation_errors']) == 0
    return {'is_approved': status}

graph = StateGraph(RubberBeamState)
graph.add_node('validate', validate_physical_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()