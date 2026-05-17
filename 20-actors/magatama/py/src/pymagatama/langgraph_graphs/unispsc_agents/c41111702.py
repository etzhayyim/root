from typing import TypedDict
from langgraph.graph import StateGraph, END

class MicroscopeState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_optics(state: MicroscopeState):
    errors = []
    if not state['spec_data'].get('magnification_range'):
        errors.append('Missing magnification specs')
    return {'validation_errors': errors}

def approval_check(state: MicroscopeState):
    approved = len(state['validation_errors']) == 0
    return {'is_approved': approved}

graph = StateGraph(MicroscopeState)
graph.add_node('validate', validate_optics)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
app = graph.compile()