from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PlaneSpecState(TypedDict):
    blade_material: str
    flatness_tolerance: float
    verified: bool

def validate_specs(state: PlaneSpecState) -> PlaneSpecState:
    if state['flatness_tolerance'] < 0.05:
        state['verified'] = True
    return state

def check_material(state: PlaneSpecState) -> PlaneSpecState:
    state['verified'] = state['blade_material'] in ['HSS', 'Carbon Steel']
    return state

builder = StateGraph(PlaneSpecState)
builder.add_node('validate', validate_specs)
builder.add_node('material', check_material)
builder.set_entry_point('validate')
builder.add_edge('validate', 'material')
builder.add_edge('material', END)
graph = builder.compile()
