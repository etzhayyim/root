from typing import TypedDict
from langgraph.graph import StateGraph, END

class WasherState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: WasherState):
    specs = state['spec_data']
    errors = []
    if not specs.get('material_grade'):
        errors.append('Missing material grade')
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

def route_by_validation(state: WasherState):
    return 'validate' if not state.get('validation_passed') else END

graph = StateGraph(WasherState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()