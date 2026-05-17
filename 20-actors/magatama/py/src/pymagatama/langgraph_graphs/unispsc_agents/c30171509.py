from typing import TypedDict
from langgraph.graph import StateGraph, END

class DoorState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_safety_specs(state: DoorState):
    errors = []
    if 'safety_standard' not in state['spec_data']:
        errors.append('Missing safety certification')
    return {'validation_errors': errors}

def approval_check(state: DoorState):
    is_ok = len(state['validation_errors']) == 0
    return {'is_approved': is_ok}

graph = StateGraph(DoorState)
graph.add_node('validate', validate_safety_specs)
graph.add_node('approval', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()