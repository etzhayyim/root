from typing import TypedDict
from langgraph.graph import StateGraph, END

class CPCState(TypedDict):
    purity: float
    safety_verified: bool
    compliant: bool

def validate_purity(state: CPCState):
    state['compliant'] = state['purity'] >= 99.0
    return state

def check_sds(state: CPCState):
    state['safety_verified'] = True
    return state

graph = StateGraph(CPCState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_sds', check_sds)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_sds')
graph.add_edge('check_sds', END)
graph = graph.compile()
