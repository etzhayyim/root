from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_id: str
    compliance_docs: List[str]
    is_approved: bool

def validate_medical_docs(state: ProcurementState):
    required = ['ISO_13485', 'Sterility_Cert']
    valid = all(doc in state['compliance_docs'] for doc in required)
    return {'is_approved': valid}

def route_by_approval(state: ProcurementState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_medical_docs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()