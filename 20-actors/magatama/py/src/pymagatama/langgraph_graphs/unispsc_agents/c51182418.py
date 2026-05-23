from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity_level: float
    safety_clearance: bool
    is_compliant: bool

def validate_purity(state: ChemicalState):
    state['is_compliant'] = state['purity_level'] >= 99.0
    return state

def check_safety_clearance(state: ChemicalState):
    state['safety_clearance'] = True
    return state

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_safety_clearance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
