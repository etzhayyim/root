from typing import TypedDict
from langgraph.graph import StateGraph, END

class BindingState(TypedDict):
    spec_data: dict
    is_valid: bool
    error_log: list

def validate_specs(state: BindingState):
    specs = state['spec_data']
    errors = []
    if not specs.get('thickness_microns'):
        errors.append('Missing thickness specification')
    return {'is_valid': len(errors) == 0, 'error_log': errors}

graph = StateGraph(BindingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
