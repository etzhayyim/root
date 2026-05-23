from typing import TypedDict
from langgraph.graph import StateGraph, END

class AirSamplerState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: AirSamplerState):
    required = ['calibration_certification', 'flow_rate_capacity']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def generate_report(state: AirSamplerState):
    status = 'APPROVED' if state['validation_passed'] else 'REJECTED'
    return {'compliance_report': f'Procurement validation status: {status}'}

graph = StateGraph(AirSamplerState)
graph.add_node('validate', validate_specs)
graph.add_node('report', generate_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()
