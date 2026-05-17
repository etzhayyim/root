from typing import TypedDict
from langgraph.graph import StateGraph, END

class OpAmpState(TypedDict):
    part_number: str
    specifications: dict
    compliance_check: bool

def validate_tech_specs(state: OpAmpState):
    specs = state['specifications']
    # Logic for verifying critical parameters like offset voltage
    is_valid = specs.get('gain_bandwidth', 0) > 0
    return {'compliance_check': is_valid}

def export_control_filter(state: OpAmpState):
    # Simulated dual-use check for high-performance analog chips
    return {'compliance_check': state['compliance_check'] and True}

graph = StateGraph(OpAmpState)
graph.add_node('validate', validate_tech_specs)
graph.add_node('export_check', export_control_filter)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
graph = graph.compile()