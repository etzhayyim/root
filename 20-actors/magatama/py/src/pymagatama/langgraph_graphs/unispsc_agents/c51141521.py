from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity: float
    gmp_verified: bool
    compliant: bool

def validate_purity(state: PharmState):
    state['compliant'] = state['purity'] >= 99.0
    return state

def check_gmp(state: PharmState):
    return {'compliant': state['compliant'] and state['gmp_verified']}

graph = StateGraph(PharmState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_gmp', check_gmp)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_gmp')
graph.add_edge('check_gmp', END)
graph = graph.compile()