from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_specs(state: RobotState):
    required = ['payload', 'reach', 'voltage']
    all_present = all(k in state['specs'] for k in required)
    return {'validated': all_present, 'compliance_report': 'Validated' if all_present else 'Missing specs'}

def export_check(state: RobotState):
    return {'compliance_report': 'Checked for dual-use export controls'}

graph = StateGraph(RobotState)
graph.add_node('validate', validate_specs)
graph.add_node('export', export_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()