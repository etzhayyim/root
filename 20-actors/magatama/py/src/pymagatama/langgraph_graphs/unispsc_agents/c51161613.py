from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    has_gmp: bool
    is_approved: bool

def validate_purity(state: ChemicalState):
    state['is_approved'] = state['purity'] >= 99.0 and state['has_gmp']
    return state

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()