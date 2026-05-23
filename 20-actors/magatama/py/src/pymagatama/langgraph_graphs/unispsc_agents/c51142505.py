from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_docs: list
    status: str

def validate_purity(state: ProcurementState):
    if state['purity_level'] >= 99.0:
        return {'status': 'purity_verified'}
    return {'status': 'purity_failed'}

def check_compliance(state: ProcurementState):
    if 'GMP_CERT' in state['compliance_docs']:
        return {'status': 'compliance_verified'}
    return {'status': 'compliance_failed'}

graph = StateGraph(ProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()
