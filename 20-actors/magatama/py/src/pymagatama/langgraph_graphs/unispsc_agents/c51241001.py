from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    purity: float
    safety_verified: bool
    storage_compliant: bool

def validate_purity(state: ChemicalProcurementState):
    state['safety_verified'] = state['purity'] >= 99.0
    return state

def check_compliance(state: ChemicalProcurementState):
    state['storage_compliant'] = True
    return state

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
