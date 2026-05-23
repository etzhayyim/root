from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: CastingState):
    errors = []
    if 'Material Grade' not in state['spec_data']: errors.append('Missing Grade')
    if not state.get('spec_data', {}).get('heat_treatment'): errors.append('Missing HT cert')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def update_status(state: CastingState):
    return {'validation_passed': True}

graph = StateGraph(CastingState)
graph.add_node('validate', validate_specs)
graph.add_node('finalizer', update_status)
graph.add_edge('validate', 'finalizer')
graph.add_edge('finalizer', END)
graph.set_entry_point('validate')
graph = graph.compile()
