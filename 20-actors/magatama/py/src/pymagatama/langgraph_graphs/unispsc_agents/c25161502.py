from typing import TypedDict
from langgraph.graph import StateGraph, END

class UnicycleState(TypedDict):
    specs: dict
    is_validated: bool

def validate_specs(state: UnicycleState):
    # Business logic for unicycle quality control
    load = state['specs'].get('load', 0)
    state['is_validated'] = load > 0 and load <= 150
    return state

builder = StateGraph(UnicycleState)
builder.add_node('validator', validate_specs)
builder.set_entry_point('validator')
builder.add_edge('validator', END)
graph = builder.compile()