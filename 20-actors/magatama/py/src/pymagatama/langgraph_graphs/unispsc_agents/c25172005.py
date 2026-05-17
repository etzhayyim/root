from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RailSystemState(TypedDict):
    part_number: str
    spec_data: dict
    is_validated: bool
    validation_errors: List[str]

def validate_specs(state: RailSystemState):
    errors = []
    if not state['spec_data'].get('load_capacity'):
        errors.append('Missing load capacity specs')
    return {'is_validated': len(errors) == 0, 'validation_errors': errors}

def route_by_validation(state: RailSystemState):
    return 'valid' if state['is_validated'] else 'invalid'

graph = StateGraph(RailSystemState)
graph.add_node('checker', validate_specs)
graph.set_entry_point('checker')
graph.add_conditional_edges('checker', route_by_validation, {'valid': END, 'invalid': END})
graph = graph.compile()