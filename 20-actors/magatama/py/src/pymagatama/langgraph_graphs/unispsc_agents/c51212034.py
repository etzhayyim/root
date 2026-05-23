from typing import TypedDict
from langgraph.graph import StateGraph, END

class CapsaicinState(TypedDict):
    purity: float
    has_sds: bool
    verified: bool

def validate_purity(state: CapsaicinState):
    state['verified'] = state['purity'] >= 98.0 and state['has_sds']
    return state

builder = StateGraph(CapsaicinState)
builder.add_node('validate', validate_purity)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
