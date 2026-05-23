from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    safety_clearance: bool
    compliant: bool

def validate_purity(state: ChemicalState):
    state['compliant'] = state['purity'] >= 99.0
    return state

def verify_safety(state: ChemicalState):
    state['safety_clearance'] = True
    return state

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', verify_safety)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
