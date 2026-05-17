from typing import TypedDict
from langgraph.graph import StateGraph, END

class SinkSpecState(TypedDict):
    material: str
    dimensions: dict
    compliance_check: bool

def validate_material(state: SinkSpecState):
    # Business logic for material validation
    state['compliance_check'] = state['material'] in ['Stainless Steel 304', 'Ceramic']
    return state

def check_dimensions(state: SinkSpecState):
    # Check for valid dimensions schema
    if 'depth' in state['dimensions'] and state['dimensions']['depth'] > 0:
        return state
    raise ValueError('Invalid depth')

builder = StateGraph(SinkSpecState)
builder.add_node('validate_material', validate_material)
builder.add_node('check_dimensions', check_dimensions)
builder.set_entry_point('validate_material')
builder.add_edge('validate_material', 'check_dimensions')
builder.add_edge('check_dimensions', END)
graph = builder.compile()