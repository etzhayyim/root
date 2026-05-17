from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class CubeState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_dimensions(state: CubeState):
    tolerance = state['spec_data'].get('tolerance', 0.05)
    actual_dev = state['spec_data'].get('deviation', 0.0)
    return {'validation_passed': actual_dev <= tolerance}

def check_material(state: CubeState):
    materials = ['acrylic', 'zinc-alloy', 'abs']
    is_valid = state['spec_data'].get('material') in materials
    return {'validation_passed': state['validation_passed'] and is_valid}

builder = StateGraph(CubeState)
builder.add_node('validate', validate_dimensions)
builder.add_node('material_check', check_material)
builder.add_edge('validate', 'material_check')
builder.add_edge('material_check', END)
builder.set_entry_point('validate')
graph = builder.compile()