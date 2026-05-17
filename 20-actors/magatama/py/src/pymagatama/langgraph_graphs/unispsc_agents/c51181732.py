from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_docs: List[str]
    status: str

def validate_purity(state: ProcurementState):
    if state['purity_level'] >= 99.0:
        return {'status': 'PASSED_PURITY'}
    return {'status': 'FAILED_PURITY'}

def verify_regulations(state: ProcurementState):
    if 'GMP_CERT' in state['compliance_docs']:
        return {'status': 'COMPLIANT'}
    return {'status': 'NON_COMPLIANT'}

graph = StateGraph(ProcurementState)
graph.add_node('check_purity', validate_purity)
graph.add_node('check_docs', verify_regulations)
graph.set_entry_point('check_purity')
graph.add_edge('check_purity', 'check_docs')
graph.add_edge('check_docs', END)
graph = graph.compile()