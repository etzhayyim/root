from typing import TypedDict
from langgraph.graph import StateGraph, END

class WeldingGraphState(TypedDict):
    spec_doc: str
    validation_passed: bool
    compliance_report: str

def validate_iso_specs(state: WeldingGraphState):
    # Simulate CAD or spec validation
    passed = 'ISO' in state['spec_doc']
    return {'validation_passed': passed}

def generate_compliance(state: WeldingGraphState):
    report = 'Compliance verified' if state['validation_passed'] else 'Manual review required'
    return {'compliance_report': report}

builder = StateGraph(WeldingGraphState)
builder.add_node('validate', validate_iso_specs)
builder.add_node('report', generate_compliance)
builder.add_edge('validate', 'report')
builder.add_edge('report', END)
builder.set_entry_point('validate')
graph = builder.compile()