from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_docs: List[str]
    approved: bool

def validate_gmp(state: ProcurementState):
    # Ensure pharmaceutical compliance
    state['approved'] = state['purity_level'] >= 99.9 and 'GMP_CERTS' in state['compliance_docs']
    return state

workflow = StateGraph(ProcurementState)
workflow.add_node('validate', validate_gmp)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()