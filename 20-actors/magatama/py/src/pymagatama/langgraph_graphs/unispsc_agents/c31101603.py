from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    material_specs: dict
    inspection_report: dict
    validation_status: bool

def validate_metallurgy(state: CastingState):
    # Simulate chemical composition validation for steel grade
    grade = state['material_specs'].get('grade')
    is_valid = grade in ['S25C', 'S45C', 'SCW480']
    return {'validation_status': is_valid}

def check_dimensions(state: CastingState):
    # Simulate dimensional tolerance verification
    return {'validation_status': state['validation_status'] and True}

builder = StateGraph(CastingState)
builder.add_node('metallurgy_check', validate_metallurgy)
builder.add_node('dimension_check', check_dimensions)
builder.add_edge('metallurgy_check', 'dimension_check')
builder.add_edge('dimension_check', END)
builder.set_entry_point('metallurgy_check')
graph = builder.compile()
