from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity_level: float
    gmp_status: bool
    is_compliant: bool

def validate_purity(state: PharmState):
    state['is_compliant'] = state['purity_level'] >= 98.0 and state['gmp_status']
    return state

graph = StateGraph(PharmState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()