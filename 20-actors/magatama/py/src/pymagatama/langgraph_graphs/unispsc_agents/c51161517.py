from typing import TypedDict
from langgraph.graph import StateGraph, END

class ZileutonState(TypedDict):
    batch_number: str
    purity_level: float
    gmp_verified: bool
    approved: bool

def validate_gmp(state: ZileutonState):
    state['gmp_verified'] = True
    return {'gmp_verified': True}

def check_purity(state: ZileutonState):
    state['approved'] = state['purity_level'] >= 99.0
    return {'approved': state['approved']}

graph = StateGraph(ZileutonState)
graph.add_node('validate_gmp', validate_gmp)
graph.add_node('check_purity', check_purity)
graph.set_entry_point('validate_gmp')
graph.add_edge('validate_gmp', 'check_purity')
graph.add_edge('check_purity', END)
graph = graph.compile()