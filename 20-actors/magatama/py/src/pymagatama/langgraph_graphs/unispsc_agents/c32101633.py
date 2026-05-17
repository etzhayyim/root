from typing import TypedDict
from langgraph.graph import StateGraph, END

class LogicGateState(TypedDict):
    part_number: str
    compliance_status: bool
    is_dual_use: bool

def check_export_control(state: LogicGateState):
    # Simulate dual-use verification logic
    state['is_dual_use'] = True if 'mil' in state['part_number'].lower() else False
    return state

def validate_specs(state: LogicGateState):
    state['compliance_status'] = True
    return state

graph = StateGraph(LogicGateState)
graph.add_node('export_check', check_export_control)
graph.add_node('spec_validation', validate_specs)
graph.set_entry_point('export_check')
graph.add_edge('export_check', 'spec_validation')
graph.add_edge('spec_validation', END)
graph = graph.compile()