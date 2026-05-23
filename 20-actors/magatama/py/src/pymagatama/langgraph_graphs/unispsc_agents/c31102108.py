from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class MoldState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_risk: str

def validate_materials(state: MoldState):
    material = state['spec_data'].get('material_composition')
    # Verify for aerospace grade compliance
    return {'validation_passed': material is not None}

def check_compliance(state: MoldState):
    return {'compliance_risk': 'low' if state['validation_passed'] else 'high'}

builder = StateGraph(MoldState)
builder.add_node('validate', validate_materials)
builder.add_node('compliance', check_compliance)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()
