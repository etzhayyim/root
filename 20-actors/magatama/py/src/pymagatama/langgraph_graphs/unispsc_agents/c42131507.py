from typing import TypedDict
from langgraph.graph import StateGraph, END

class PatientSlipperState(TypedDict):
    slipper_type: str
    material: str
    slip_resistance: float
    compliant: bool

def validate_physics(state: PatientSlipperState):
    state['compliant'] = state['slip_resistance'] >= 0.4
    return state

def check_compliance(state: PatientSlipperState):
    return 'compliant_node' if state['compliant'] else 'reject_node'

graph = StateGraph(PatientSlipperState)
graph.add_node('validate', validate_physics)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', check_compliance, {'compliant_node': END, 'reject_node': END})
graph.compile()