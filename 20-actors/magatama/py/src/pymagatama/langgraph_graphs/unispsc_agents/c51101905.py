from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChloroquineState(TypedDict):
    purity: float
    gmp_verified: bool
    approved: bool

def validate_quality(state: ChloroquineState):
    state['approved'] = state['purity'] >= 0.99 and state['gmp_verified']
    return state

graph = StateGraph(ChloroquineState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
