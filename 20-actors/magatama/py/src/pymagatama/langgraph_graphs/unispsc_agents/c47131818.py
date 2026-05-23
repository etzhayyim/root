from typing import TypedDict
from langgraph.graph import StateGraph, END

class SanitizerState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: SanitizerState):
    cadr = state['specs'].get('cadr', 0)
    state['validation_passed'] = cadr > 200
    state['compliance_report'] = 'Pass' if state['validation_passed'] else 'Fail: CADR too low'
    return state

builder = StateGraph(SanitizerState)
builder.add_node('validate', validate_specs)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
