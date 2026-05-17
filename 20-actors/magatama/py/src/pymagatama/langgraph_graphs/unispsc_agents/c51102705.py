from typing import TypedDict
from langgraph.graph import StateGraph, END

class CetrimideState(TypedDict):
    purity: float
    safety_compliant: bool
    approved: bool

def validate_purity(state: CetrimideState):
    state['approved'] = state['purity'] >= 99.0
    return state

def check_sds(state: CetrimideState):
    if not state.get('safety_compliant', False):
        state['approved'] = False
    return state

graph = StateGraph(CetrimideState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_sds', check_sds)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_sds')
graph.add_edge('check_sds', END)
graph = graph.compile()