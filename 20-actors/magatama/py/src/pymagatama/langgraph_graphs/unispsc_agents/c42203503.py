from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_id: str
    sterile_cert: bool
    compliance_docs: List[str]
    approved: bool

def validate_certification(state: ProcurementState):
    state['approved'] = state['sterile_cert'] and 'ISO_13485' in state['compliance_docs']
    return state

workflow = StateGraph(ProcurementState)
workflow.add_node('cert_validation', validate_certification)
workflow.set_entry_point('cert_validation')
workflow.add_edge('cert_validation', END)
graph = workflow.compile()