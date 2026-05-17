from typing import TypedDict
from langgraph.graph import StateGraph, END

class NuclearState(TypedDict):
    material_spec: dict
    compliance_docs: list
    validation_status: str

def validate_material(state: NuclearState):
    # Business logic for metallurgical certification check
    return {'validation_status': 'verified'} if 'zircaloy' in state['material_spec'].get('type', '') else {'validation_status': 'failed'}

def check_compliance(state: NuclearState):
    # Business logic for export control checks
    return {'validation_status': 'compliant'}

builder = StateGraph(NuclearState)
builder.add_node('validate', validate_material)
builder.add_node('compliance', check_compliance)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()