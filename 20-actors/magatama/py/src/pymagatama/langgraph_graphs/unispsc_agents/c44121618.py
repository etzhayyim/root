from typing import TypedDict
from langgraph.graph import StateGraph, END

class ScissorsState(TypedDict):
    blade_material: str
    blade_length_mm: float
    has_safety_lock: bool
    is_approved: bool

def validate_scissors(state: ScissorsState):
    state['is_approved'] = state['blade_length_mm'] > 0 and state['blade_material'] is not None
    return state

builder = StateGraph(ScissorsState)
builder.add_node('validate', validate_scissors)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
