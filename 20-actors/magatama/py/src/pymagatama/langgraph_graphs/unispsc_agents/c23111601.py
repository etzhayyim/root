from typing import TypedDict
from langgraph.graph import StateGraph, END

class LaserProcurementState(TypedDict):
    spec_sheet: dict
    compliance_cleared: bool
    inspection_required: bool

def validate_laser_specs(state: LaserProcurementState):
    power = state['spec_sheet'].get('power_kw', 0)
    state['compliance_cleared'] = power > 0 and power < 20
    return state

def check_export_controls(state: LaserProcurementState):
    state['inspection_required'] = state['compliance_cleared']
    return state

builder = StateGraph(LaserProcurementState)
builder.add_node('validate_specs', validate_laser_specs)
builder.add_node('export_check', check_export_controls)
builder.set_entry_point('validate_specs')
builder.add_edge('validate_specs', 'export_check')
builder.add_edge('export_check', END)
graph = builder.compile()