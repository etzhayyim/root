from typing import TypedDict
from langgraph.graph import StateGraph, END

class HousingState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_specs(state: HousingState):
    errors = []
    if not state['spec_data'].get('ip_rating'):
        errors.append('Missing IP rating')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def route_by_validation(state: HousingState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(HousingState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
