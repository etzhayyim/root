from typing import TypedDict
from langgraph.graph import StateGraph, END

class TubingState(TypedDict):
    material: str
    pressure_rating: float
    compliant: bool

def validate_specs(state: TubingState):
    # Business logic for tubing validation
    if state['material'] == 'latex':
        state['compliant'] = False
    else:
        state['compliant'] = True
    return state

builder = StateGraph(TubingState)
builder.add_node('validation', validate_specs)
builder.set_entry_point('validation')
builder.add_edge('validation', END)
graph = builder.compile()