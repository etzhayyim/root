from langgraph.graph import StateGraph, END
from typing import TypedDict

class GentianVioletState(TypedDict):
    purity: float
    hazard_check: bool
    approved: bool

def validate_purity(state: GentianVioletState):
    state['approved'] = state['purity'] >= 99.0
    return state

def check_hazard(state: GentianVioletState):
    state['hazard_check'] = True
    return state

graph = StateGraph(GentianVioletState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', check_hazard)
graph.set_entry_point('safety')
graph.add_edge('safety', 'validate')
graph.add_edge('validate', END)
graph = graph.compile()