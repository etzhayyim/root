from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    compliance_docs: List[str]
    is_approved: bool

def validate_safety_certs(state: ProcurementState):
    required = ['Toxicity Report', 'ISO Certification']
    all_present = all(doc in state['compliance_docs'] for doc in required)
    return {'is_approved': all_present}

def route_by_compliance(state: ProcurementState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_safety_certs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'approved': END, 'rejected': END})
graph.compile()
