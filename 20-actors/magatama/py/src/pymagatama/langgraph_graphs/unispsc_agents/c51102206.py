from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity: float
    temp_stable: bool
    compliant: bool

def check_purity(state: PharmState):
    state['compliant'] = state['purity'] >= 99.0
    return 'compliant_check'

def check_stability(state: PharmState):
    return {'temp_stable': True}

graph = StateGraph(PharmState)
graph.add_node('verify_purity', check_purity)
graph.add_node('verify_storage', check_stability)
graph.set_entry_point('verify_purity')
graph.add_edge('verify_purity', 'verify_storage')
graph.add_edge('verify_storage', END)
graph = graph.compile()