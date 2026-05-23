from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    api_name: str
    purity_check: bool
    gmp_verified: bool
    is_compliant: bool

def validate_gmp(state: PharmState):
    state['gmp_verified'] = True
    return 'gmp_check_complete'

def check_purity(state: PharmState):
    state['purity_check'] = True
    state['is_compliant'] = True
    return 'purity_check_complete'

graph = StateGraph(PharmState)
graph.add_node('gmp', validate_gmp)
graph.add_node('purity', check_purity)
graph.add_edge('gmp', 'purity')
graph.add_edge('purity', END)
graph.set_entry_point('gmp')
compiled_graph = graph.compile()
