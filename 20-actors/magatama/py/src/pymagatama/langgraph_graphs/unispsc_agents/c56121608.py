from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CotsState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_safety(state: CotsState):
    spacing = state['spec_data'].get('slat_spacing', 0)
    if 45 <= spacing <= 65:
        state['validation_passed'] = True
        state['compliance_report'] = 'Validation Successful'
    else:
        state['validation_passed'] = False
        state['compliance_report'] = 'Safety Violation: Slat spacing invalid'
    return state

builder = StateGraph(CotsState)
builder.add_node('safety_check', validate_safety)
builder.set_entry_point('safety_check')
builder.add_edge('safety_check', END)
graph = builder.compile()