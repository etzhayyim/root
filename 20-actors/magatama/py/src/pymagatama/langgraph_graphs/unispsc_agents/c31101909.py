from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CastState(TypedDict):
    part_id: str
    material: str
    specs: dict
    approved: bool

def validate_alloy(state: CastState) -> CastState:
    # Simulate high precision metallurgical check for tin alloys
    state['approved'] = state['specs'].get('tin_purity', 0) > 0.99
    return state

def check_geometry(state: CastState) -> CastState:
    # Simulate dimensional validation
    if state.get('approved', False):
        state['approved'] = 'tolerance' in state['specs']
    return state

builder = StateGraph(CastState)
builder.add_node('alloy_check', validate_alloy)
builder.add_node('geom_check', check_geometry)
builder.set_entry_point('alloy_check')
builder.add_edge('alloy_check', 'geom_check')
builder.add_edge('geom_check', END)
graph = builder.compile()