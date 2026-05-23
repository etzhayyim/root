from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LightState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: LightState) -> LightState:
    required = ['IP Rating', 'Lumens', 'Safety Certification']
    state['validation_passed'] = all(k in state['specs'] for k in required)
    state['compliance_report'] = 'Validation Successful' if state['validation_passed'] else 'Missing Required Specs'
    return state

def run_compliance(state: LightState) -> LightState:
    if state['validation_passed']:
        state['compliance_report'] = 'Safety standards met for portable duty.'
    return state

graph = StateGraph(LightState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', run_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
