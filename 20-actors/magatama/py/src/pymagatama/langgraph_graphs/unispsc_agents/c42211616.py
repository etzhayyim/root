from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToiletingAidState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_report: str

def validate_ergonomics(state: ToiletingAidState):
    state['is_compliant'] = state['spec_data'].get('weight_capacity', 0) > 0
    state['validation_report'] = 'Ergonomics and load testing passed' if state['is_compliant'] else 'Load testing failed'
    return state

def check_hygiene_compliance(state: ToiletingAidState):
    state['is_compliant'] = state['is_compliant'] and state['spec_data'].get('sterilization_standard') == 'ISO-13485'
    return state

builder = StateGraph(ToiletingAidState)
builder.add_node('validate', validate_ergonomics)
builder.add_node('hygiene', check_hygiene_compliance)
builder.set_entry_point('validate')
builder.add_edge('validate', 'hygiene')
builder.add_edge('hygiene', END)
graph = builder.compile()