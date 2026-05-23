from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_level: float
    has_gmp_cert: bool
    is_compliant: bool

def validate_purity(state: ProcurementState):
    state['is_compliant'] = state['purity_level'] >= 99.0 and state['has_gmp_cert']
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', END)
graph = graph.compile()
