from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_level: float
    has_gmp_cert: bool
    approved: bool

def validate_purity(state: ProcurementState):
    state['approved'] = state['purity_level'] >= 99.5 and state['has_gmp_cert']
    return state

builder = StateGraph(ProcurementState)
builder.add_node('validate', validate_purity)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
