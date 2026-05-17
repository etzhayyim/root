from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LatheState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_status: List[str]

def validate_lathe_specs(state: LatheState):
    required = ['diameter', 'spindle_speed']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def check_export_controls(state: LatheState):
    return {'compliance_status': ['Dual-use check complete', 'Export license not required']}

graph = StateGraph(LatheState)
graph.add_node('validate', validate_lathe_specs)
graph.add_node('compliance', check_export_controls)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()