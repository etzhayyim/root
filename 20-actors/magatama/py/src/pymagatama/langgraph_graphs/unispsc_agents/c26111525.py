from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DrumMotorState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: DrumMotorState):
    errors = []
    if state['specs'].get('IP_rating', 0) < 54:
        errors.append('Insufficient IP rating for industrial environment.')
    return {'validation_errors': errors}

def approval_check(state: DrumMotorState):
    approved = len(state['validation_errors']) == 0
    return {'is_approved': approved}

graph = StateGraph(DrumMotorState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()