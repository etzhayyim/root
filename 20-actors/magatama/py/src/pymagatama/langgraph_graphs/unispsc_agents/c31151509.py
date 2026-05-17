from typing import TypedDict
from langgraph.graph import StateGraph, END

class RubberState(TypedDict):
    diameter: float
    tensile_strength: float
    compliance_passed: bool

def validate_specs(state: RubberState):
    state['compliance_passed'] = state['diameter'] > 0 and state['tensile_strength'] > 5.0
    return state

builder = StateGraph(RubberState)
builder.add_node('validation', validate_specs)
builder.set_entry_point('validation')
builder.add_edge('validation', END)
graph = builder.compile()