from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity: float
    has_gmp: bool
    is_verified: bool

def validate_quality(state: PharmState):
    state['is_verified'] = state['purity'] >= 99.0 and state['has_gmp']
    return state

graph = StateGraph(PharmState)
graph.add_node('validation', validate_quality)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()
