from typing import TypedDict
from langgraph.graph import StateGraph, END

class RadiationCounterState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_detector_specs(state: RadiationCounterState):
    required = ['efficiency', 'voltage']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def generate_compliance(state: RadiationCounterState):
    if state['validation_passed']:
        return {'compliance_report': 'Safety check: PASS - Compliance with nuclear regulations verified.'}
    return {'compliance_report': 'Safety check: FAIL - Missing critical calibration metrics.'}

graph = StateGraph(RadiationCounterState)
graph.add_node('validate', validate_detector_specs)
graph.add_node('compliance', generate_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()