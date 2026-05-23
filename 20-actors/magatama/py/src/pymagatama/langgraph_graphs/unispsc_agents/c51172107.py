from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    gmp_valid: bool
    approved: bool

def validate_gmp(state: ProcurementState):
    state['gmp_valid'] = True
    return state

def check_purity(state: ProcurementState):
    state['approved'] = state['purity_level'] >= 99.0
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_gmp', validate_gmp)
graph.add_node('check_purity', check_purity)
graph.set_entry_point('validate_gmp')
graph.add_edge('validate_gmp', 'check_purity')
graph.add_edge('check_purity', END)
graph = graph.compile()
