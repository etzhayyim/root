from typing import TypedDict
from langgraph.graph import StateGraph, END

class AircraftComponentState(TypedDict):
    part_number: str
    tso_compliant: bool
    safety_check_passed: bool

def validate_tso(state: AircraftComponentState):
    state['tso_compliant'] = state['part_number'].startswith('TSO-C22')
    return state

def perform_safety_audit(state: AircraftComponentState):
    state['safety_check_passed'] = state['tso_compliant']
    return state

builder = StateGraph(AircraftComponentState)
builder.add_node('validate_tso', validate_tso)
builder.add_node('safety_audit', perform_safety_audit)
builder.add_edge('validate_tso', 'safety_audit')
builder.add_edge('safety_audit', END)
builder.set_entry_point('validate_tso')
graph = builder.compile()
