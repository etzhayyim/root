from typing import TypedDict
from langgraph.graph import StateGraph, END

class OxaceprolState(TypedDict):
    purity: float
    gmp_verified: bool
    compliant: bool

def validate_purity(state: OxaceprolState):
    state['compliant'] = state['purity'] >= 99.0
    return state

def check_gmp(state: OxaceprolState):
    return {'compliant': state['compliant'] and state['gmp_verified']}

graph = StateGraph(OxaceprolState)
graph.add_node('validate', validate_purity)
graph.add_node('gmp_check', check_gmp)
graph.set_entry_point('validate')
graph.add_edge('validate', 'gmp_check')
graph.add_edge('gmp_check', END)
graph = graph.compile()