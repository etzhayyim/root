from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    purity: float
    has_gmp_cert: bool
    is_approved: bool

def validate_purity(state: ProcurementState):
    state['is_approved'] = state['purity'] >= 99.0 and state['has_gmp_cert']
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
