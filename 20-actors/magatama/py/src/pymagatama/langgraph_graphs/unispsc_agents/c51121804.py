from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    storage_temp: float
    is_gmp_certified: bool
    approved: bool

def validate_purity(state: ProcurementState):
    state['approved'] = state['purity'] >= 99.0
    return state

def check_gmp(state: ProcurementState):
    state['approved'] = state['approved'] and state['is_gmp_certified']
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_gmp', check_gmp)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_gmp')
graph.add_edge('check_gmp', END)
graph = graph.compile()
