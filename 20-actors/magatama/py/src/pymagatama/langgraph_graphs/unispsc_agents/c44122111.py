from typing import TypedDict
from langgraph.graph import StateGraph, END

class ReinforcementState(TypedDict):
    spec_data: dict
    validation_issues: list
    status: str

def validate_dimensions(state: ReinforcementState):
    inner = state['spec_data'].get('inner_diameter_mm', 0)
    if inner < 6.0: 
        state['validation_issues'].append('Inner diameter too small for standard binders')
    return {'status': 'validated' if not state['validation_issues'] else 'rejected'}

builder = StateGraph(ReinforcementState)
builder.add_node('validate', validate_dimensions)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()