from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity: float
    gmp_valid: bool
    approved: bool

def validate_purity(state: PharmState) -> PharmState:
    state['approved'] = state['purity'] >= 99.0 and state['gmp_valid']
    return state

graph_builder = StateGraph(PharmState)
graph_builder.add_node('validate', validate_purity)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', END)
graph = graph_builder.compile()
