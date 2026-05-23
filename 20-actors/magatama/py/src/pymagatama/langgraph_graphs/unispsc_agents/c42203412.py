from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StentProcurementState(TypedDict):
    item_id: str
    quality_docs: List[str]
    compliance_passed: bool

def validate_compliance(state: StentProcurementState):
    required = ['ISO_13485', 'Regulatory_Clearance']
    passed = all(doc in state['quality_docs'] for doc in required)
    return {'compliance_passed': passed}

def route_by_compliance(state: StentProcurementState):
    return 'process' if state['compliance_passed'] else 'reject'

graph = StateGraph(StentProcurementState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'process': END, 'reject': END})
graph.compile()
