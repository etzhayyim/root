from typing import TypedDict
from langgraph.graph import StateGraph, END

class PureeState(TypedDict):
    quality_docs: dict
    approved: bool
    brix: float

def validate_purity(state: PureeState):
    state['approved'] = state['brix'] >= 10.0
    return state

workflow = StateGraph(PureeState)
workflow.add_node('validate', validate_purity)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()