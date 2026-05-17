from typing import TypedDict
from langgraph.graph import StateGraph, END

class PulpProcessState(TypedDict):
    moisture_level: float
    quality_cert: bool
    is_compliant: bool

def validate_specs(state: PulpProcessState):
    state['is_compliant'] = state['moisture_level'] < 12.0 and state['quality_cert']
    return state

builder = StateGraph(PulpProcessState)
builder.add_node('validate', validate_specs)
builder.add_edge('validate', END)
builder.set_entry_point('validate')
graph = builder.compile()