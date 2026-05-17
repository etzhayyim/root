from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: CastingState):
    specs = state['spec_data']
    errors = []
    if 'material' not in specs: errors.append('Missing material grade')
    if 'tolerance' not in specs: errors.append('Missing tolerance range')
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

def route_by_validation(state: CastingState):
    return 'validate' if not state.get('validation_passed') else END

graph = StateGraph(CastingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()