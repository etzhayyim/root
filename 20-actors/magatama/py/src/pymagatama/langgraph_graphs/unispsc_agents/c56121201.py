from typing import TypedDict
from langgraph.graph import StateGraph, END

class CouchState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_spec(state: CouchState):
    required = ['weight_capacity_kg', 'antibacterial_iso_certification']
    state['is_compliant'] = all(k in state['spec_data'] for k in required)
    return state

builder = StateGraph(CouchState)
builder.add_node('validation', validate_spec)
builder.set_entry_point('validation')
builder.add_edge('validation', END)
graph = builder.compile()
