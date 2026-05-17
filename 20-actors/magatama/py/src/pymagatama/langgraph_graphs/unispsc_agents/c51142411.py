from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    drug_name: str
    purity_level: float
    gmp_verified: bool
    approved: bool

def validate_purity(state: ProcurementState):
    state['approved'] = state['purity_level'] >= 99.0 and state['gmp_verified']
    return state

workflow = StateGraph(ProcurementState)
workflow.add_node('validation', validate_purity)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()