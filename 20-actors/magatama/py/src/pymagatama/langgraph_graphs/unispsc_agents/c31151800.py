from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WireState(TypedDict):
    specs: dict
    validation_result: bool
    compliance_report: str

def validate_specs(state: WireState):
    required = ['Material Grade', 'Tensile Strength (MPa)']
    valid = all(k in state['specs'] for k in required)
    return {**state, 'validation_result': valid, 'compliance_report': 'Validated' if valid else 'Incomplete'}

def export_control_check(state: WireState):
    # Dual-use logic check
    alert = 'High-tensile status' in str(state['specs'])
    return {**state, 'compliance_report': 'Alert: Export Control' if alert else 'Passed'}

graph = StateGraph(WireState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', export_control_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()