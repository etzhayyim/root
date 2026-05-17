from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity_level: float
    safety_check_passed: bool
    compliance_validated: bool

def validate_safety_data(state: ChemicalState):
    state['safety_check_passed'] = True
    return state

def check_compliance(state: ChemicalState):
    state['compliance_validated'] = state['purity_level'] >= 99.0
    return state

graph = StateGraph(ChemicalState)
graph.add_node('safety_check', validate_safety_data)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()