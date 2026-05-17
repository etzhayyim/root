from typing import TypedDict
from langgraph.graph import StateGraph, END

class BrakeState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_torque(state: BrakeState):
    torque = state['spec_data'].get('torque', 0)
    if torque <= 0:
        state['validation_errors'].append('Invalid torque value')
    return state

def check_compliance(state: BrakeState):
    state['is_approved'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(BrakeState)
graph.add_node('validate', validate_torque)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()