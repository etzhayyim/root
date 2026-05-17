from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    part_number: str
    compatibility_verified: bool
    compliance_checked: bool

def validate_compatibility(state: ProcurementState):
    print(f'Checking compatibility for {state['part_number']}')
    return {'compatibility_verified': True}

def check_material_compliance(state: ProcurementState):
    print('Validating material safety standards')
    return {'compliance_checked': True}

builder = StateGraph(ProcurementState)
builder.add_node('compatibility', validate_compatibility)
builder.add_node('compliance', check_material_compliance)
builder.set_entry_point('compatibility')
builder.add_edge('compatibility', 'compliance')
builder.add_edge('compliance', END)
graph = builder.compile()