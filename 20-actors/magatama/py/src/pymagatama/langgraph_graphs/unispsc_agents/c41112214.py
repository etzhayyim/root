from typing import TypedDict
from langgraph.graph import StateGraph, END

class ControllerState(TypedDict):
    temp_range: float
    precision: float
    calibration_cert: bool
    approved: bool

def validate_specs(state: ControllerState):
    state['approved'] = state['temp_range'] >= 1.0 and state['precision'] <= 0.01
    return state

def check_compliance(state: ControllerState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(ControllerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', check_compliance, {'approved': END, 'rejected': END})
graph.compile()
