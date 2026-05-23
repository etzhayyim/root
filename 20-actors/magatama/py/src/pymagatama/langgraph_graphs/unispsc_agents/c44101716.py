from typing import TypedDict
from langgraph.graph import StateGraph, END

class PuncherState(TypedDict):
    spec_data: dict
    is_valid: bool

def validate_punch_capacity(state: PuncherState):
    capacity = state['spec_data'].get('capacity', 0)
    return {'is_valid': capacity > 0}

def check_safety_compliance(state: PuncherState):
    compliant = state['spec_data'].get('safety_cert', False)
    return {'is_valid': state['is_valid'] and compliant}

graph = StateGraph(PuncherState)
graph.add_node('capacity_check', validate_punch_capacity)
graph.add_node('safety_check', check_safety_compliance)
graph.set_entry_point('capacity_check')
graph.add_edge('capacity_check', 'safety_check')
graph.add_edge('safety_check', END)
graph = graph.compile()
