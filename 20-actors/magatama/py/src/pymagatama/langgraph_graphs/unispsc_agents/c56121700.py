from typing import TypedDict
from langgraph.graph import StateGraph, END

class ClassroomStorageState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_safety_specs(state: ClassroomStorageState):
    errors = []
    if 'anti_tip' not in state['spec_data']:
        errors.append('Missing mandatory anti-tip functionality.')
    return {'validation_errors': errors}

def approval_check(state: ClassroomStorageState):
    approved = len(state['validation_errors']) == 0
    return {'is_approved': approved}

graph = StateGraph(ClassroomStorageState)
graph.add_node('validate', validate_safety_specs)
graph.add_node('approval', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
app = graph.compile()