from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    purity: float
    gmp_status: bool
    verified: bool

def validate_purity(state: PharmaState):
    state['verified'] = state['purity'] >= 0.99 and state['gmp_status']
    return state

graph = StateGraph(PharmaState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

compiled_graph = graph.compile()
