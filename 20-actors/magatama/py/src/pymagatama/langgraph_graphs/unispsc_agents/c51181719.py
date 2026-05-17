from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    purity_level: float
    has_coa: bool
    compliance_status: str

def validate_quality(state: PharmaState) -> PharmaState:
    if state['purity_level'] >= 99.0 and state['has_coa']:
        state['compliance_status'] = 'APPROVED'
    else:
        state['compliance_status'] = 'REJECTED'
    return state

workflow = StateGraph(PharmaState)
workflow.add_node('validate', validate_quality)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()