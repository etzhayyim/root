from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AdenosineState(TypedDict):
    purity: float
    coa_verified: bool
    compliant: bool

def validate_purity(state: AdenosineState):
    state['compliant'] = state['purity'] >= 99.0
    return state

def check_coa(state: AdenosineState):
    if not state['coa_verified']:
        state['compliant'] = False
    return state

graph = StateGraph(AdenosineState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_coa', check_coa)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_coa')
graph.add_edge('check_coa', END)
graph = graph.compile()
