from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    batch_id: str
    gmp_verified: bool
    purity_level: float
    status: str

def check_compliance(state: PharmaState):
    is_compliant = state['gmp_verified'] and state['purity_level'] >= 99.0
    return {'status': 'APPROVED' if is_compliant else 'REJECTED'}

workflow = StateGraph(PharmaState)
workflow.add_node('compliance_check', check_compliance)
workflow.set_entry_point('compliance_check')
workflow.add_edge('compliance_check', END)
graph = workflow.compile()