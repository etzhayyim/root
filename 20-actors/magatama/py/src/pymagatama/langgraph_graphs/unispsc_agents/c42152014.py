from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TracerState(TypedDict):
    isotope: str
    activity_bq: float
    safety_clearance: bool
    compliant: bool

def validate_safety(state: TracerState):
    state['safety_clearance'] = state['activity_bq'] < 1000.0
    return state

def compliance_check(state: TracerState):
    state['compliant'] = state['safety_clearance'] and (state['isotope'] != 'restricted_variant')
    return state

graph = StateGraph(tracer_state=TracerState)
graph.add_node('validate', validate_safety)
graph.add_node('compliance', compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()