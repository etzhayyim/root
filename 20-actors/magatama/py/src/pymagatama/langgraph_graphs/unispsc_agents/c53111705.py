from typing import TypedDict
from langgraph.graph import StateGraph, END

class InfantSlipperState(TypedDict):
    material_safety_test: bool
    slip_resistance_index: float
    compliance_report: str

def validate_material(state: InfantSlipperState):
    return {'material_safety_test': True}

def check_slip_hazard(state: InfantSlipperState):
    is_safe = state['slip_resistance_index'] >= 0.4
    return {'compliance_report': 'Passed' if is_safe else 'Failed'}

builder = StateGraph(InfantSlipperState)
builder.add_node('validate_material', validate_material)
builder.add_node('check_slip', check_slip_hazard)
builder.add_edge('validate_material', 'check_slip')
builder.add_edge('check_slip', END)
builder.set_entry_point('validate_material')
graph = builder.compile()
