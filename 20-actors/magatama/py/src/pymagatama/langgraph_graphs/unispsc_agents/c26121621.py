from typing import TypedDict
from langgraph.graph import StateGraph

class KaptanCableState(TypedDict):
    spec_sheet: dict
    validation_results: dict

def validate_thermal_spec(state: KaptanCableState):
    temp_range = state['spec_sheet'].get('temp_range', 0)
    valid = temp_range >= 200
    return {'validation_results': {'thermal_pass': valid}}

def check_compliance(state: KaptanCableState):
    compliance = state['spec_sheet'].get('mil_spec_standard', False)
    return {'validation_results': {'compliance_pass': compliance}}

builder = StateGraph(KaptanCableState)
builder.add_node('thermal_val', validate_thermal_spec)
builder.add_node('compliance_val', check_compliance)
builder.set_entry_point('thermal_val')
builder.add_edge('thermal_val', 'compliance_val')
builder.add_edge('compliance_val', '__end__')
graph = builder.compile()