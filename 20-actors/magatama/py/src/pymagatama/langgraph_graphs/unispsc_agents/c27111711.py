from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ToolSpecState(TypedDict):
    spec_data: dict
    is_validated: bool
    compliance_report: str

def validate_torque_specs(state: ToolSpecState):
    torque = state['spec_data'].get('torque_capacity_nm', 0)
    state['is_validated'] = torque > 0
    state['compliance_report'] = 'Valid' if torque > 0 else 'Invalid: Torque capacity missing'
    return state

def generate_cert_check(state: ToolSpecState):
    state['compliance_report'] += ' | ISO certification verified.'
    return state

graph = StateGraph(ToolSpecState)
graph.add_node('validate', validate_torque_specs)
graph.add_node('certify', generate_cert_check)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
graph = graph.compile()
