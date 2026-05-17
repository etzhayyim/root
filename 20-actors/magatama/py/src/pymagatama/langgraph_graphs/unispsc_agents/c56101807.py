from typing import TypedDict
from langgraph.graph import StateGraph, END

class BouncerState(TypedDict):
    safety_certs: list
    weight_limit: float
    inspection_passed: bool

def validate_safety(state: BouncerState):
    state['inspection_passed'] = 'ASTM_F2167' in state['safety_certs']
    return state

builder = StateGraph(BouncerState)
builder.add_node('policy_check', validate_safety)
builder.set_entry_point('policy_check')
builder.add_edge('policy_check', END)
graph = builder.compile()