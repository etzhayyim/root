from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    safety_check: bool
    hazard_compliant: bool

def validate_purity(state: ChemicalState):
    state['safety_check'] = state['purity'] >= 99.0
    return state

def check_hazard_regulations(state: ChemicalState):
    state['hazard_compliant'] = True
    return state

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_hazard_regulations)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()