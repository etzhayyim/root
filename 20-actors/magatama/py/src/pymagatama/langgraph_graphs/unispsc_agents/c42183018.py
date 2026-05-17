from typing import TypedDict
from langgraph.graph import StateGraph, END

class TonometerState(TypedDict):
    spec_data: dict
    validation_results: dict

def validate_compliance(state: TonometerState):
    # Simulate regulatory validation for ophthalmic medical device
    cert = state['spec_data'].get('certificate')
    return {'validation_results': {'status': 'PASS' if cert else 'FAIL'}}

def check_calibration(state: TonometerState):
    # Validate calibration date
    return {'validation_results': {'calibration_valid': True}}

builder = StateGraph(TonometerState)
builder.add_node('compliance', validate_compliance)
builder.add_node('calibration', check_calibration)
builder.set_entry_point('compliance')
builder.add_edge('compliance', 'calibration')
builder.add_edge('calibration', END)
graph = builder.compile()