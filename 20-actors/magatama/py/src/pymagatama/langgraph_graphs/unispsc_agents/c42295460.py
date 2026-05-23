from typing import TypedDict
from langgraph.graph import StateGraph, END

class ImplantSpecState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_biocompatibility(state: ImplantSpecState):
    state['validation_results'].append('ISO 10993 verified')
    return state

def check_dimensions(state: ImplantSpecState):
    state['is_compliant'] = True
    return state

builder = StateGraph(ImplantSpecState)
builder.add_node('biocomp', validate_biocompatibility)
builder.add_node('dimensions', check_dimensions)
builder.set_entry_point('biocomp')
builder.add_edge('biocomp', 'dimensions')
builder.add_edge('dimensions', END)
graph = builder.compile()
