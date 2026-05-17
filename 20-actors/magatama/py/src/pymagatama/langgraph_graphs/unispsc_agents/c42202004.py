from langgraph.graph import StateGraph, END
from typing import TypedDict

class LymphaticWorkflowState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_risk: str

def validate_collimator_specs(state: LymphaticWorkflowState):
    radiation_rating = state['spec_data'].get('radiation_attenuation', 0)
    state['validation_passed'] = radiation_rating > 95.0
    return state

def check_regulatory_compliance(state: LymphaticWorkflowState):
    state['compliance_risk'] = 'high' if state['spec_data'].get('sterile') == False else 'low'
    return state

graph = StateGraph(LymphaticWorkflowState)
graph.add_node('validate', validate_collimator_specs)
graph.add_node('compliance', check_regulatory_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()