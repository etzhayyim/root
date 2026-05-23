from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    gmp_verified: bool
    compliance_status: str

def validate_quality(state: ProcurementState):
    state['compliance_status'] = 'PASS' if state['purity'] >= 99.0 and state['gmp_verified'] else 'FAIL'
    return state

builder = StateGraph(ProcurementState)
builder.add_node('validate', validate_quality)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
