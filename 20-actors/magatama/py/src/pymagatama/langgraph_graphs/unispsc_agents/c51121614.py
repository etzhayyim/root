from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    gmp_status: bool
    approved: bool

def validate_purity(state: ProcurementState):
    state['approved'] = state['purity'] >= 99.0
    return state

def verify_gmp(state: ProcurementState):
    state['approved'] = state['approved'] and state['gmp_status']
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('verify_gmp', verify_gmp)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'verify_gmp')
graph.add_edge('verify_gmp', END)
graph = graph.compile()