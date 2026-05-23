from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    gmp_status: bool
    is_compliant: bool

def validate_purity(state: ProcurementState):
    state['is_compliant'] = state['purity_level'] >= 99.0
    return state

def check_gmp(state: ProcurementState):
    if not state.get('gmp_status'):
        state['is_compliant'] = False
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_gmp', check_gmp)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_gmp')
graph.add_edge('check_gmp', END)
graph = graph.compile()
