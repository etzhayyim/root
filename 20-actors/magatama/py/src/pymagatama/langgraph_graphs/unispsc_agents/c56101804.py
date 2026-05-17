from langgraph.graph import StateGraph, END
from typing import TypedDict

class CribProcurementState(TypedDict):
    spec_data: dict
    safety_compliance: bool
    approved: bool

def validate_safety_standards(state: CribProcurementState):
    standards = state['spec_data'].get('safety_certification_standard', [])
    is_compliant = 'ASTM-F1169' in standards or 'EN-716' in standards
    return {'safety_compliance': is_compliant}

def approve_procurement(state: CribProcurementState):
    return {'approved': state['safety_compliance']}

builder = StateGraph(CribProcurementState)
builder.add_node('validate', validate_safety_standards)
builder.add_node('approve', approve_procurement)
builder.add_edge('validate', 'approve')
builder.add_edge('approve', END)
builder.set_entry_point('validate')
graph = builder.compile()