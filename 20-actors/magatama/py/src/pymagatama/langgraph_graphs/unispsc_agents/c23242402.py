from typing import TypedDict
from langgraph.graph import StateGraph, END

class MachineSpecState(TypedDict):
    spec_data: dict
    validation_passed: bool
    is_dual_use: bool

def validate_tech_specs(state: MachineSpecState):
    state['validation_passed'] = 'spindle_torque' in state['spec_data']
    return state

def export_control_check(state: MachineSpecState):
    state['is_dual_use'] = state['spec_data'].get('axes_count', 0) >= 5
    return state

graph = StateGraph(MachineSpecState)
graph.add_node('validate', validate_tech_specs)
graph.add_node('export_check', export_control_check)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
graph = graph.compile()