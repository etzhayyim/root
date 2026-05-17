from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlooringState(TypedDict):
    material_type: str
    thickness: float
    iso_compliance: bool
    approved: bool

def validate_specs(state: FlooringState):
    state['approved'] = state['thickness'] >= 4.0 and state['iso_compliance']
    return state

builder = StateGraph(FlooringState)
builder.add_node('validate', validate_specs)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()