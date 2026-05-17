from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class HydraulicState(TypedDict):
    spec_data: dict
    validation_log: Annotated[list, operator.add]
    is_approved: bool

def validate_pressure_specs(state: HydraulicState):
    pressure = state['spec_data'].get('max_operating_pressure_mpa', 0)
    if pressure > 70:
        return {'validation_log': ['High pressure category: requires secondary safety review'], 'is_approved': True}
    return {'validation_log': ['Standard pressure spec verified'], 'is_approved': True}

def check_compliance(state: HydraulicState):
    if 'iso_certification_code' not in state['spec_data']:
        return {'validation_log': ['Compliance failed: ISO missing'], 'is_approved': False}
    return {'validation_log': ['Compliance verified'], 'is_approved': True}

builder = StateGraph(HydraulicState)
builder.add_node('validate_pressure', validate_pressure_specs)
builder.add_node('check_compliance', check_compliance)
builder.add_edge('validate_pressure', 'check_compliance')
builder.add_edge('check_compliance', END)
builder.set_entry_point('validate_pressure')
graph = builder.compile()