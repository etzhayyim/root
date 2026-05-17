from typing import TypedDict
from langgraph.graph import StateGraph, END

class LightSpecState(TypedDict):
    voltage: str
    ip_rating: str
    compliance_code: str
    is_compliant: bool

def validate_specs(state: LightSpecState):
    state['is_compliant'] = state['ip_rating'] >= 'IP65' and state['compliance_code'] != ''
    return state

builder = StateGraph(LightSpecState)
builder.add_node('validate', validate_specs)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()