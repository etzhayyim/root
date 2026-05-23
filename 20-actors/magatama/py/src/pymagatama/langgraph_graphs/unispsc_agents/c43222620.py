from typing import TypedDict
from langgraph.graph import StateGraph, END

class SwitchState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_specs(state: SwitchState):
    required = ['throughput', 'port_density']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid, 'compliance_report': 'Passed' if valid else 'Failed'}

def route_by_validation(state: SwitchState):
    return 'process' if state['validated'] else END

builder = StateGraph(SwitchState)
builder.add_node('validate', validate_specs)
builder.add_edge('__start__', 'validate')
builder.add_edge('validate', END)
graph = builder.compile()
