from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    purity_level: float
    compliance_docs: List[str]
    is_approved: bool

def validate_pharma_specs(state: ProcurementState):
    # Business logic for Etofenamate purity and regulatory verification
    is_valid = state['purity_level'] >= 99.0 and 'GMP_CERT' in state['compliance_docs']
    return {'is_approved': is_valid}

def finalize_procurement(state: ProcurementState):
    status = 'Approved' if state['is_approved'] else 'Rejected'
    return {'status': status}

builder = StateGraph(ProcurementState)
builder.add_node('validate', validate_pharma_specs)
builder.add_node('finalize', finalize_procurement)
builder.set_entry_point('validate')
builder.add_edge('validate', 'finalize')
builder.add_edge('finalize', END)
graph = builder.compile()
