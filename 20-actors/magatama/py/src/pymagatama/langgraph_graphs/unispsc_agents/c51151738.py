from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmaProcurementState(TypedDict):
    purity: float
    has_gmp_cert: bool
    approved: bool

def validate_purity(state: PharmaProcurementState):
    state['approved'] = state['purity'] >= 99.0 and state['has_gmp_cert']
    return state

workflow = StateGraph(PharmaProcurementState)
workflow.add_node('validate', validate_purity)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()