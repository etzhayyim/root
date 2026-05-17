from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_specs: dict
    compliance_passed: bool

def validate_materials(state: ProcurementState):
    # Business logic for medical material validation
    is_compliant = all(key in state['material_specs'] for key in ['composition', 'sterility'])
    return {'compliance_passed': is_compliant}

def approval_step(state: ProcurementState):
    print('Proceeding to quality control.')
    return {}

builder = StateGraph(ProcurementState)
builder.add_node('validate', validate_materials)
builder.add_node('approve', approval_step)
builder.add_edge('validate', 'approve')
builder.add_edge('approve', END)
builder.set_entry_point('validate')
graph = builder.compile()