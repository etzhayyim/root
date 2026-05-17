from typing import TypedDict
from langgraph.graph import StateGraph, END

class DryerState(TypedDict):
    specs: dict
    validation_errors: list
    is_compliant: bool

def validate_dryer_specs(state: DryerState):
    errors = []
    if state['specs'].get('capacity', 0) <= 0:
        errors.append('Invalid drum capacity')
    if 'energy_rating' not in state['specs']:
        errors.append('Missing energy efficiency certification')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(DryerState)
graph.add_node('validate', validate_dryer_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()