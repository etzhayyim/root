from typing import TypedDict
from langgraph.graph import StateGraph, END

class SterilizationState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_thermal_spec(state: SterilizationState):
    temp_rating = state['spec_data'].get('temp_celsius', 0)
    state['validation_passed'] = temp_rating >= 134
    if not state['validation_passed']:
        state['error_log'].append('Temperature rating insufficient for standard autoclaving.')
    return state

def check_compliance(state: SterilizationState):
    state['validation_passed'] = state['validation_passed'] and state['spec_data'].get('iso_11607', False)
    return state

graph = StateGraph(SterilizationState)
graph.add_node('thermal_check', validate_thermal_spec)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('thermal_check')
graph.add_edge('thermal_check', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()