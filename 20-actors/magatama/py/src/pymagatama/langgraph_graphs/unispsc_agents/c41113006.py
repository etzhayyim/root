from typing import TypedDict
from langgraph.graph import StateGraph, END

class RadiometryState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: RadiometryState):
    required = ['Spectral Range', 'Calibration']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def generate_report(state: RadiometryState):
    report = "Standard compliance report for radiometry analytical instruments." if state['validation_passed'] else "Validation failed."
    return {'compliance_report': report}

graph = StateGraph(RadiometryState)
graph.add_node('validate', validate_specs)
graph.add_node('report', generate_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()
