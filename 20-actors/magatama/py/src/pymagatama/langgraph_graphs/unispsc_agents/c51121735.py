from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity: float
    gmp_status: bool
    batch_id: str
    compliance_ok: bool

def validate_purity(state: PharmState) -> PharmState:
    state['compliance_ok'] = state['purity'] >= 99.0
    return state

builder = StateGraph(PharmState)
builder.add_node('validate', validate_purity)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()