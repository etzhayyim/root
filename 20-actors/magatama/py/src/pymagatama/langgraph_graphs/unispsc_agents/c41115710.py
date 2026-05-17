from typing import TypedDict
from langgraph.graph import StateGraph, END

class GCColumnState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_column_specs(state: GCColumnState):
    errors = []
    required = ['length', 'id', 'phase']
    for field in required:
        if field not in state['spec_data']:
            errors.append(f'Missing {field}')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(GCColumnState)
graph.add_node('validate', validate_column_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()