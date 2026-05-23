from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PullerState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_puller(state: PullerState):
    errors = []
    if state['spec_data'].get('pulling_force', 0) <= 0:
        errors.append('Invalid pulling force capacity.')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(PullerState)
graph.add_node('validate', validate_puller)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
