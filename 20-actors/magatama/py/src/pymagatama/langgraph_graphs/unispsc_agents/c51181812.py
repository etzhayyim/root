from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_check: bool
    regulatory_approval: bool
    status: str

def validate_purity(state: ProcurementState):
    # Simulated HPLC analysis logic for Dienestrol
    return {'status': 'PURITY_VALIDATED' if state['purity_check'] else 'PURITY_FAILED'}

def check_compliance(state: ProcurementState):
    return {'status': 'COMPLIANCE_VERIFIED' if state['regulatory_approval'] else 'COMPLIANCE_FAILED'}

builder = StateGraph(ProcurementState)
builder.add_node('validate', validate_purity)
builder.add_node('compliance', check_compliance)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()