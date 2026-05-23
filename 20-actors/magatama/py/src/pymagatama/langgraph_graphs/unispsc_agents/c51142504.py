from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    api_purity: float
    compliance_docs: list
    storage_temp: str

def validate_purity(state: ProcurementState):
    assert state['api_purity'] >= 99.0, 'Purity below threshold'
    return {'status': 'validated'}

def check_compliance(state: ProcurementState):
    return {'compliant': len(state['compliance_docs']) > 0}

builder = StateGraph(ProcurementState)
builder.add_node('validate', validate_purity)
builder.add_node('compliance', check_compliance)
builder.set_entry_point('validate')
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
graph = builder.compile()
