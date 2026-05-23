from typing import TypedDict
from langgraph.graph import StateGraph, END

class MatState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_physical_specs(state: MatState):
    errors = []
    if state['spec_data'].get('slip_resistance_rating', 0) < 0.6:
        errors.append('Insufficient slip resistance rating')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(MatState)
graph.add_node('validate', validate_physical_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
