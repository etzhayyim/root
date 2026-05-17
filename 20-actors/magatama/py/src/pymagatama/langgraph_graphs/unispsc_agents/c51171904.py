from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity: float
    gmp_status: bool
    compliant: bool

def validate_purity(state: PharmState):
    state['compliant'] = state['purity'] >= 99.0 and state['gmp_status']
    return state

builder = StateGraph(PharmState)
builder.add_node('validate', validate_purity)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()