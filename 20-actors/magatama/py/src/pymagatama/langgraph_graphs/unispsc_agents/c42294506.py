from typing import TypedDict
from langgraph.graph import StateGraph, END

class OphthalmicToolState(TypedDict):
    tool_id: str
    material_spec: str
    sterilization_validated: bool
    compliance_cleared: bool

def validate_material(state: OphthalmicToolState):
    # Check for medical grade titanium or stainless steel
    is_valid = state['material_spec'] in ['Titanium', '316L Stainless Steel']
    return {'compliance_cleared': is_valid}

def check_sterilization(state: OphthalmicToolState):
    return {'sterilization_validated': True}

builder = StateGraph(OphthalmicToolState)
builder.add_node('validate', validate_material)
builder.add_node('sterilize', check_sterilization)
builder.add_edge('validate', 'sterilize')
builder.add_edge('sterilize', END)
builder.set_entry_point('validate')
graph = builder.compile()