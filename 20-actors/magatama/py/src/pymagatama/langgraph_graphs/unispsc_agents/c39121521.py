from typing import TypedDict
from langgraph.graph import StateGraph, END

class MotorStarterState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: MotorStarterState):
    required = ['voltage', 'amperage', 'ip_rating']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed, 'compliance_report': 'Success' if passed else 'Missing specs'}

def approval_step(state: MotorStarterState):
    return {'compliance_report': 'Final Approval Granted'}

graph = StateGraph(MotorStarterState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()