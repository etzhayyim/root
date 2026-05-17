from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrainSpecState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_drain_specs(state: DrainSpecState):
    errors = []
    if 'Material Grade' not in state['spec_data']: errors.append('Missing Material Grade')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(DrainSpecState)
graph.add_node('validate', validate_drain_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()