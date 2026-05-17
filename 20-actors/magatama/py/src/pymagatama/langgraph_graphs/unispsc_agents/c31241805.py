from typing import TypedDict
from langgraph.graph import StateGraph, END

class FilterState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_optics(state: FilterState):
    # Perform optical validation logic
    c_wl = state['spec_data'].get('CWL', 0)
    state['validation_passed'] = bool(c_wl > 0)
    return state

builder = StateGraph(FilterState)
builder.add_node('validate', validate_optics)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()