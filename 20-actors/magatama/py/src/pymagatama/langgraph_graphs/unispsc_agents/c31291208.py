from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class MagnesiumState(TypedDict):
    spec_sheet: dict
    validation_errors: List[str]
    is_approved: bool

def validate_alloy_grade(state: MagnesiumState):
    grade = state['spec_sheet'].get('grade')
    if grade not in ['AZ31B', 'ZK60A']:
        state['validation_errors'].append('Unsupported magnesium alloy grade')
    return state

def check_surface_finish(state: MagnesiumState):
    if not state.get('spec_sheet', {}).get('anodization_certified', False):
        state['validation_errors'].append('Missing mandatory corrosion protection certification')
    return state

builder = StateGraph(MagnesiumState)
builder.add_node('validate_grade', validate_alloy_grade)
builder.add_node('check_finish', check_surface_finish)
builder.add_edge('validate_grade', 'check_finish')
builder.add_edge('check_finish', END)
builder.set_entry_point('validate_grade')
graph = builder.compile()
