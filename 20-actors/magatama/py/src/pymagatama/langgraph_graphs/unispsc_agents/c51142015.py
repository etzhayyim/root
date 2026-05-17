from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    has_msds: bool
    is_compliant: bool

def validate_purity(state: ChemicalState):
    state['is_compliant'] = state['purity'] >= 99.0 and state['has_msds']
    return state

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()