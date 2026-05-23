from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcureState(TypedDict):
    purity_level: float
    has_gmp: bool
    approved: bool

def validate_purity(state: ProcureState):
    state['approved'] = state['purity_level'] >= 99.0 and state['has_gmp']
    return state

graph = StateGraph(ProcureState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
