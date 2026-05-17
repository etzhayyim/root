from typing import TypedDict
from langgraph.graph import StateGraph, END

class PressureVesselState(TypedDict):
    pressure: float
    cert_valid: bool
    approved: bool

def validate_pressure(state: PressureVesselState):
    state['cert_valid'] = state['pressure'] > 0 and state['pressure'] < 50.0
    return state

def check_compliance(state: PressureVesselState):
    state['approved'] = state['cert_valid']
    return state

graph = StateGraph(PressureVesselState)
graph.add_node('validate', validate_pressure)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()