from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    gmp_certified: bool
    approved: bool

def validate_quality(state: ProcurementState):
    state['approved'] = state['purity'] >= 99.0 and state['gmp_certified']
    return state

workflow = StateGraph(ProcurementState)
workflow.add_node('validate', validate_quality)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
