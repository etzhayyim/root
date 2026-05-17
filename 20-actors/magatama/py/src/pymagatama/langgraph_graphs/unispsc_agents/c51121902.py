from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity: float
    gmp_certified: bool
    approved: bool

def validate_purity(state: ProcurementState):
    state['approved'] = state['purity'] >= 99.0 and state['gmp_certified']
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()