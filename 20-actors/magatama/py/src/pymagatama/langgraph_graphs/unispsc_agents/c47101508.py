from typing import TypedDict
from langgraph.graph import StateGraph, END

class DesalinationState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_report: str

def validate_specs(state: DesalinationState):
    capacity = state['spec_data'].get('capacity', 0)
    state['validated'] = capacity > 0
    return state

def generate_compliance(state: DesalinationState):
    state['compliance_report'] = 'Standard compliant' if state['validated'] else 'Invalid specifications'
    return state

workflow = StateGraph(DesalinationState)
workflow.add_node('validate', validate_specs)
workflow.add_node('compliance', generate_compliance)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'compliance')
workflow.add_edge('compliance', END)
graph = workflow.compile()