from typing import TypedDict
from langgraph.graph import StateGraph, END

class RespiratoryCompState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: RespiratoryCompState):
    required = ['MedicalDeviceCertification', 'FlowRateLPM']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def check_compliance(state: RespiratoryCompState):
    if state.get('validation_passed'):
        return 'compliance_check'
    return END

graph = StateGraph(RespiratoryCompState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()