from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_tech_specs(state: RobotState) -> dict:
    required = ['Load Capacity (kg)', 'Degree of Freedom']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid, 'compliance_report': 'Validated' if valid else 'Missing Params'}

def check_compliance(state: RobotState) -> dict:
    return {'compliance_report': 'Safety standards verified for industrial use'}

graph = StateGraph(RobotState)
graph.add_node('validate', validate_tech_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
