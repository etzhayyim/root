from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    purity: float
    gmp_valid: bool
    approved: bool

def validate_quality(state: PharmaState):
    state['approved'] = state['purity'] >= 99.0 and state['gmp_valid']
    return state

workflow = StateGraph(PharmaState)
workflow.add_node('validation', validate_quality)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()