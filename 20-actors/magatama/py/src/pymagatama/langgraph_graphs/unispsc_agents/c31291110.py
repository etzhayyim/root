from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    specs: dict
    validation_passed: bool
    error_log: list

def validate_material(state: ExtrusionState):
    state['validation_passed'] = 'material_type' in state['specs']
    return state

def check_tolerances(state: ExtrusionState):
    if state['validation_passed']:
        state['validation_passed'] = state['specs'].get('tolerance', 0) < 0.05
    return state

builder = StateGraph(ExtrusionState)
builder.add_node('validate', validate_material)
builder.add_node('tolerance_check', check_tolerances)
builder.set_entry_point('validate')
builder.add_edge('validate', 'tolerance_check')
builder.add_edge('tolerance_check', END)
graph = builder.compile()