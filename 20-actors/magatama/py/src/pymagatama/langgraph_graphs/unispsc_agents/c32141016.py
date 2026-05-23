from typing import TypedDict
from langgraph.graph import StateGraph, END

class ValveState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_report: str

def validate_specs(state: ValveState):
    required = ['voltage', 'pin_config']
    is_valid = all(k in state['spec_data'] for k in required)
    return {'validated': is_valid, 'compliance_report': 'Success' if is_valid else 'Missing specs'}

def check_export_control(state: ValveState):
    return {'compliance_report': 'Dual-use check passed'}

graph = StateGraph(ValveState)
graph.add_node('validate', validate_specs)
graph.add_node('export', check_export_control)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()
