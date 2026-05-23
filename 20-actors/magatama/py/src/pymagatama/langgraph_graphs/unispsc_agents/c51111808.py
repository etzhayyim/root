from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    compliance_docs: List[str]
    is_approved: bool

def validate_compliance(state: ProcurementState):
    required = ['GMP', 'SDS', 'CoA']
    all_present = all(doc in state['compliance_docs'] for doc in required)
    return {'is_approved': all_present}

def route_procurement(state: ProcurementState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
