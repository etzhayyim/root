from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    purity: float
    safety_checked: bool
    approved: bool

def validate_purity(state: ChemicalProcurementState):
    state['approved'] = state['purity'] >= 99.0
    return state

def verify_safety(state: ChemicalProcurementState):
    state['safety_checked'] = True
    return state

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', verify_safety)
graph.set_entry_point('safety')
graph.add_edge('safety', 'validate')
graph.add_edge('validate', END)
graph = graph.compile()