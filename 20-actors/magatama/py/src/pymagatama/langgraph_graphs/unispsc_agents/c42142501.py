from typing import TypedDict
from langgraph.graph import StateGraph, END

class AmnioNeedleState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_medical_specs(state: AmnioNeedleState):
    required = ['gauge', 'length', 'iso_cert', 'lot_number']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed, 'compliance_report': 'Success' if passed else 'Missing Specs'}

def finalize_order(state: AmnioNeedleState):
    return {'compliance_report': 'Order ready for medical audit'}

builder = StateGraph(AmnioNeedleState)
builder.add_node('validate', validate_medical_specs)
builder.add_node('finalize', finalize_order)
builder.add_edge('validate', 'finalize')
builder.set_entry_point('validate')
builder.add_edge('finalize', END)
graph = builder.compile()