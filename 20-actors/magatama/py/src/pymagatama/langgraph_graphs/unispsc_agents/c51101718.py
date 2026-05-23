from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    purity_level: float
    compliant: bool
    safety_check: bool

def validate_purity(state: ChemicalProcurementState):
    state['compliant'] = state['purity_level'] >= 99.0
    return state

def check_msds(state: ChemicalProcurementState):
    state['safety_check'] = True
    return state

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_msds', check_msds)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_msds')
graph.add_edge('check_msds', END)
graph.compile()
