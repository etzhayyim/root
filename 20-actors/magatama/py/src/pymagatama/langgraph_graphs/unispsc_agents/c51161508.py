from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    batch_id: str
    purity_level: float
    gmp_verified: bool
    approved: bool

def validate_purity(state: PharmaState):
    state['approved'] = state['purity_level'] >= 99.0
    return state

def check_gmp(state: PharmaState):
    return state

graph = StateGraph(PharmaState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_gmp', check_gmp)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_gmp')
graph.add_edge('check_gmp', END)
graph = graph.compile()