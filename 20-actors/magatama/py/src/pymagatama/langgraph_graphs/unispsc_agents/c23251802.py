from typing import TypedDict
from langgraph.graph import StateGraph, END

class DieState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: DieState):
    hardness = state['specs'].get('hardness', 0)
    state['approved'] = hardness >= 58
    return state

builder = StateGraph(DieState)
builder.add_node('validate', validate_specs)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
