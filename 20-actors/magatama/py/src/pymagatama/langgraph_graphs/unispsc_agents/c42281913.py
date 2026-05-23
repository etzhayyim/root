from typing import TypedDict
from langgraph.graph import StateGraph, END

class SterilizationState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_materials(state: SterilizationState):
    is_valid = state['spec_data'].get('fda_approved', False)
    return {'validation_passed': is_valid}

def generate_report(state: SterilizationState):
    return {'compliance_report': 'ISO compliant' if state['validation_passed'] else 'Failed'}

graph = StateGraph(SterilizationState)
graph.add_node('validate', validate_materials)
graph.add_node('report', generate_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()
