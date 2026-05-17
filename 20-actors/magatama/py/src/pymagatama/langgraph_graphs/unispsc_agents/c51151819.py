from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    compliance_docs: bool
    is_approved: bool

def validate_purity(state: ProcurementState):
    state['is_approved'] = state['purity'] >= 99.0 and state['compliance_docs']
    return state

builder = StateGraph(ProcurementState)
builder.add_node('validation', validate_purity)
builder.set_entry_point('validation')
builder.add_edge('validation', END)
graph = builder.compile()