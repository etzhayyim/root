from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PegboardState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_hook_specs(state: PegboardState):
    errors = []
    if state['spec_data'].get('weight_capacity', 0) <= 0:
        errors.append('Weight capacity must be a positive number.')
    state['validation_errors'] = errors
    state['is_approved'] = len(errors) == 0
    return state

graph = StateGraph(PegboardState)
graph.add_node('validate', validate_hook_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compile = graph.compile()
