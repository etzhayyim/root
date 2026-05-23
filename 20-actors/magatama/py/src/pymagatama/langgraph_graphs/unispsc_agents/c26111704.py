from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChargerState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_voltage(state: ChargerState):
    volts = state['spec_data'].get('voltage', 0)
    state['is_compliant'] = 100 <= volts <= 240
    return state

def check_certifications(state: ChargerState):
    certs = state['spec_data'].get('certs', [])
    if not any(c in certs for c in ['UL', 'CE', 'PSE']):
        state['is_compliant'] = False
    return state

builder = StateGraph(ChargerState)
builder.add_node('validate_voltage', validate_voltage)
builder.add_node('check_certifications', check_certifications)
builder.set_entry_point('validate_voltage')
builder.add_edge('validate_voltage', 'check_certifications')
builder.add_edge('check_certifications', END)
graph = builder.compile()
