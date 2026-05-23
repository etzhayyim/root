from typing import TypedDict
from langgraph.graph import StateGraph, END

class CamFollowerState(TypedDict):
    spec_data: dict
    validation_checks: list
    approval_status: bool

def validate_load_capacity(state: CamFollowerState):
    load = state['spec_data'].get('load_rating')
    is_valid = load > 0
    return {'validation_checks': ['load_capacity_check'], 'approval_status': is_valid}

def check_dual_use(state: CamFollowerState):
    # Logic for dual-use control vetting
    return {'validation_checks': state['validation_checks'] + ['export_control_verified']}

graph = StateGraph(CamFollowerState)
graph.add_node('validate_load', validate_load_capacity)
graph.add_node('check_export', check_dual_use)
graph.set_entry_point('validate_load')
graph.add_edge('validate_load', 'check_export')
graph.add_edge('check_export', END)
app = graph.compile()
