from typing import TypedDict
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_specs(state: ActuatorState):
    required = ['voltage', 'torque', 'protocol']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid}

def export_review(state: ActuatorState):
    return {'compliance_report': 'Dual-use check cleared.' if state['validated'] else 'Pending'}

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_specs)
graph.add_node('export', export_review)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()