from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    safety_verified: bool
    compliance_report: str

def validate_specs(state: ChemicalState):
    state['safety_verified'] = state['purity'] >= 99.0
    return state

def generate_compliance(state: ChemicalState):
    state['compliance_report'] = 'Grade A Compliant' if state['safety_verified'] else 'Rejected'
    return state

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', generate_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
