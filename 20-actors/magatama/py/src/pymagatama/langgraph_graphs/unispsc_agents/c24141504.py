from typing import TypedDict, List
from langgraph.graph import StateGraph, END
class SealState(TypedDict):
    seal_id: str
    tamper_verified: bool
    compliance_docs: List[str]
    status: str
def validate_seal_spec(state: SealState):
    return {'tamper_verified': True, 'status': 'VALIDATED'}
def check_compliance(state: SealState):
    return {'status': 'COMPLIANT' if len(state['compliance_docs']) > 0 else 'NON-COMPLIANT'}
graph = StateGraph(SealState)
graph.add_node('validate', validate_seal_spec)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
app = graph.compile()