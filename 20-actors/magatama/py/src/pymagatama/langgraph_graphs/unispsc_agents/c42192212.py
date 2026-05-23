from typing import TypedDict
from langgraph.graph import StateGraph, END

class TransferMatState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_mat_specs(state: TransferMatState):
    errors = []
    if state['spec_data'].get('weight_capacity', 0) < 150:
        errors.append('Weight capacity below standard requirement')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_verification(state: TransferMatState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(TransferMatState)
graph.add_node('validate', validate_mat_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
