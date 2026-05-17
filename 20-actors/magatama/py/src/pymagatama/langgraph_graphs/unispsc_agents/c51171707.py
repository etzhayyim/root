from typing import TypedDict
from langgraph.graph import StateGraph, END

class BismuthState(TypedDict):
    purity: float
    compliance_docs: bool
    is_approved: bool

def validate_purity(state: BismuthState):
    state['is_approved'] = state['purity'] >= 99.0 and state['compliance_docs']
    return state

graph = StateGraph(BismuthState)
graph.add_node('validation', validate_purity)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()