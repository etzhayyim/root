from typing import TypedDict
from langgraph.graph import StateGraph, END

class ZotepineState(TypedDict):
    purity: float
    has_coa: bool
    approved: bool

def validate_purity(state: ZotepineState) -> ZotepineState:
    state['approved'] = state['purity'] >= 99.0 and state['has_coa']
    return state

graph = StateGraph(ZotepineState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
