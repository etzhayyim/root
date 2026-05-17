from typing import TypedDict
from langgraph.graph import StateGraph, END

class SpectroState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_risk: str

def validate_specs(state: SpectroState):
    # Business logic for instrument validation
    required = ['Wavelength_Range', 'Sensitivity_SNR']
    valid = all(k in state['spec_data'] for k in required)
    return {'validated': valid, 'compliance_risk': 'low' if valid else 'high'}

def route_by_risk(state: SpectroState):
    return 'check' if state['compliance_risk'] == 'high' else END

graph = StateGraph(SpectroState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()