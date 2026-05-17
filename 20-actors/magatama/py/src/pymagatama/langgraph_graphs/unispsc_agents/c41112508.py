from langgraph.graph import StateGraph, END
from typing import TypedDict

class GaugeState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: GaugeState):
    required = ['Pressure Range', 'Accuracy Class', 'Explosion-proof Rating']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def generate_compliance(state: GaugeState):
    report = 'Full compliance check completed' if state['validation_passed'] else 'Manual review required'
    return {'compliance_report': report}

graph = StateGraph(GaugeState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', generate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()