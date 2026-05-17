from typing import TypedDict
from langgraph.graph import StateGraph, END

class FittingState(TypedDict):
    spec_data: dict
    validation_result: bool

def validate_pressure_rating(state: FittingState):
    rating = state['spec_data'].get('pressure_psi', 0)
    return {'validation_result': rating > 0}

def structural_integrity_check(state: FittingState):
    return state

builder = StateGraph(FittingState)
builder.add_node('validate_pressure', validate_pressure_rating)
builder.add_node('integrity_check', structural_integrity_check)
builder.add_edge('validate_pressure', 'integrity_check')
builder.add_edge('integrity_check', END)
builder.set_entry_point('validate_pressure')
graph = builder.compile()