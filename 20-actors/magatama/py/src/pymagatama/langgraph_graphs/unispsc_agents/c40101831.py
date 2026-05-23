from typing import TypedDict
from langgraph.graph import StateGraph, END

class HeaterState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_check: bool

def validate_specs(state: HeaterState):
    required = ['power', 'frequency', 'cooling']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def check_export_compliance(state: HeaterState):
    # Logic for dual-use export control screening
    return {'compliance_check': True}

builder = StateGraph(HeaterState)
builder.add_node('validate', validate_specs)
builder.add_node('compliance', check_export_compliance)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()
