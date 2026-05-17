from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MeloxicamState(TypedDict):
    purity: float
    gmp_status: bool
    compliant: bool

def validate_purity(state: MeloxicamState) -> MeloxicamState:
    state['compliant'] = state['purity'] >= 99.0 and state['gmp_status']
    return state

workflow = StateGraph(MeloxicamState)
workflow.add_node('validation', validate_purity)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()