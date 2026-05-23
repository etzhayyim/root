from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_name: str
    compliance_docs: List[str]
    validation_passed: bool

def validate_compliance(state: ProcurementState):
    required = ['Certificate of Analysis', 'Regulatory License']
    passed = all(doc in state['compliance_docs'] for doc in required)
    return {'validation_passed': passed}

def route_procurement(state: ProcurementState):
    return 'process' if state['validation_passed'] else 'reject'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_procurement, {'process': END, 'reject': END})
