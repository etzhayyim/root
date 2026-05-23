from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_dimensions(state: CastingState):
    # Simulate CAD/Tolerance validation logic
    tolerance = state['spec_data'].get('tolerance', 0.05)
    passed = tolerance <= 0.1
    return {'validation_passed': passed}

def check_material_compliance(state: CastingState):
    # Simulate material composition check
    return {'validation_passed': state['validation_passed']}

builder = StateGraph(CastingState)
builder.add_node('validate_cad', validate_dimensions)
builder.add_node('check_material', check_material_compliance)
builder.set_entry_point('validate_cad')
builder.add_edge('validate_cad', 'check_material')
builder.add_edge('check_material', END)
graph = builder.compile()
