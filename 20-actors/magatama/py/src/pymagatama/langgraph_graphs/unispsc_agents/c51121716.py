from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    gmp_valid: bool
    approved: bool

def validate_quality(state: ProcurementState):
    state['approved'] = state['purity'] >= 99.0 and state['gmp_valid']
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()