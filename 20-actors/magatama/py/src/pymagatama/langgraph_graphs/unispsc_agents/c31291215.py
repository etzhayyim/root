from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_tin_specs(state: ExtrusionState):
    errors = []
    if state['spec_data'].get('purity', 0) < 99.9:
        errors.append('Purity below industry standard')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def route_by_approval(state: ExtrusionState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(ExtrusionState)
graph.add_node('validator', validate_tin_specs)
graph.add_edge('validator', END)
graph.set_entry_point('validator')
compiled_graph = graph.compile()
