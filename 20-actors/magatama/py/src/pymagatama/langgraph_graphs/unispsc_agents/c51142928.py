from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    api_purity: float
    compliance_docs: bool
    is_approved: bool

def validate_purity(state: ProcurementState):
    state['is_approved'] = state['api_purity'] >= 99.0 and state['compliance_docs']
    return state

builder = StateGraph(ProcurementState)
builder.add_node('validate_api', validate_purity)
builder.set_entry_point('validate_api')
builder.add_edge('validate_api', END)
graph = builder.compile()
