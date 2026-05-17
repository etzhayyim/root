from typing import TypedDict
from langgraph.graph import StateGraph, END

class EnvironmentalState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_status: str

def validate_specs(state: EnvironmentalState):
    required_keys = ['thermal_load_capacity', 'energy_efficiency_rating']
    state['validation_passed'] = all(k in state['specs'] for k in required_keys)
    return state

def check_compliance(state: EnvironmentalState):
    state['compliance_status'] = 'COMPLIANT' if state['validation_passed'] else 'NON_COMPLIANT'
    return state

graph = StateGraph(EnvironmentalState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()