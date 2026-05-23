from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_id: str
    compliance_docs: List[str]
    status: str

def validate_compliance(state: ProcurementState):
    required = ['iso13485', 'fda_clearance']
    valid = all(doc in state['compliance_docs'] for doc in required)
    return {'status': 'processed' if valid else 'rejected'}

builder = StateGraph(ProcurementState)
builder.add_node('compliance', validate_compliance)
builder.set_entry_point('compliance')
builder.add_edge('compliance', END)
graph = builder.compile()
