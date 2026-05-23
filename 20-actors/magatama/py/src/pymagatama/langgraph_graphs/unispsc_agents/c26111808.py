from typing import TypedDict
from langgraph.graph import StateGraph, END

class TrantorqueState(TypedDict):
    spec_data: dict
    is_valid: bool
    error_msg: str

def validate_torque_specs(state: TrantorqueState):
    torque = state['spec_data'].get('torque_capacity', 0)
    if torque > 0: return {'is_valid': True}
    return {'is_valid': False, 'error_msg': 'Invalid torque capacity'}

def check_compliance(state: TrantorqueState):
    compliant = state['spec_data'].get('iso_compliant', False)
    return {'is_valid': compliant}

graph = StateGraph(TrantorqueState)
graph.add_node('validate', validate_torque_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
