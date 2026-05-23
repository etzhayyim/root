from typing import TypedDict
from langgraph.graph import StateGraph, END

class PedalSpecState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_specs(state: PedalSpecState):
    errors = []
    required = ['Axle Material', 'Thread Size']
    for field in required:
        if field not in state['spec_data']:
            errors.append(f'Missing field: {field}')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def route_by_validation(state: PedalSpecState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(PedalSpecState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

compiled_graph = graph.compile()
