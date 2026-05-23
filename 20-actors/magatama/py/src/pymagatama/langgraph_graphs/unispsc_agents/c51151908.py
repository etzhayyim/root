from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    compliance_docs: list
    status: str

def validate_purity(state: ProcurementState):
    is_valid = state['purity'] >= 99.0
    return {'status': 'PASSED' if is_valid else 'REJECTED'}

def check_compliance(state: ProcurementState):
    has_gmp = 'GMP_CERT' in state['compliance_docs']
    return {'status': 'COMPLIANT' if has_gmp else 'NON_COMPLIANT'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
