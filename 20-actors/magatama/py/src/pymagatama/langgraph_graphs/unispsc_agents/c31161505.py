from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SetScrewState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_dimensions(state: SetScrewState):
    errors = []
    if state['spec_data'].get('thread_pitch') is None:
        errors.append('Missing required thread pitch specification.')
    return {'validation_errors': errors}

def approval_check(state: SetScrewState):
    status = len(state['validation_errors']) == 0
    return {'is_approved': status}

graph = StateGraph(SetScrewState)
graph.add_node('validate', validate_dimensions)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
