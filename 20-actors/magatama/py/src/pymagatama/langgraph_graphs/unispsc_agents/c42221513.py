from typing import TypedDict
from langgraph.graph import StateGraph, END

class CatheterState(TypedDict):
    kit_id: str
    sterility_verified: bool
    compliance_docs: list
    approval_status: str

def check_compliance(state: CatheterState):
    docs = [d.lower() for d in state['compliance_docs']]
    if 'iso13485' in docs and 'fda_clearance' in docs:
        return {'approval_status': 'COMPLIANT'}
    return {'approval_status': 'PENDING_REVIEW'}

def verify_sterility(state: CatheterState):
    return {'sterility_verified': True}

graph = StateGraph(CatheterState)
graph.add_node('verify_sterility', verify_sterility)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('verify_sterility')
graph.add_edge('verify_sterility', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()
