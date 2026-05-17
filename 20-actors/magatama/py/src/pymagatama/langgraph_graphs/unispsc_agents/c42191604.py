from typing import TypedDict
from langgraph.graph import StateGraph, END

class MonitorArmState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_load_capacity(state: MonitorArmState):
    load = state['spec_data'].get('load_capacity', 0)
    state['validation_passed'] = load > 0
    return state

def check_medical_compliance(state: MonitorArmState):
    state['compliance_report'] = 'ISO 13485 Verified' if state['validation_passed'] else 'Compliance Failed'
    return state

graph = StateGraph(MonitorArmState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('compliance', check_medical_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()