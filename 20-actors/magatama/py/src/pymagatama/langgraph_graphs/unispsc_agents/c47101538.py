from typing import TypedDict
from langgraph.graph import StateGraph, END

class DigesterState(TypedDict):
    capacity: float
    material: str
    validation_status: bool

def validate_specs(state: DigesterState):
    state['validation_status'] = state['capacity'] > 0 and len(state.get('material', '')) > 0
    return state

builder = StateGraph(DigesterState)
builder.add_node('validate', validate_specs)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
