from typing import TypedDict
from langgraph.graph import StateGraph, END
class PharmaProcurementState(TypedDict):
    purity_level: float
    gmp_status: bool
    compliance_docs: list
    is_approved: bool
def validate_quality(state: PharmaProcurementState):
    if state['purity_level'] >= 99.0 and state['gmp_status']:
        return {'is_approved': True}
    return {'is_approved': False}
def verify_compliance(state: PharmaProcurementState):
    required = ['SDS', 'CoA', 'GMP_Cert']
    all_docs = all(doc in state['compliance_docs'] for doc in required)
    return {'is_approved': all_docs}
builder = StateGraph(PharmaProcurementState)
builder.add_node('quality_check', validate_quality)
builder.add_node('compliance_check', verify_compliance)
builder.set_entry_point('quality_check')
builder.add_edge('quality_check', 'compliance_check')
builder.add_edge('compliance_check', END)
graph = builder.compile()