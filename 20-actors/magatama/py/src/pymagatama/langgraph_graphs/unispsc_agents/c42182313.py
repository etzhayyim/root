from typing import TypedDict
from langgraph.graph import StateGraph, END

class NeuroDiagnosticState(TypedDict):
    device_id: str
    compliance_verified: bool
    inspection_passed: bool

def validate_compliance(state: NeuroDiagnosticState):
    print(f'Validating medical compliance for {state["device_id"]}')
    return {'compliance_verified': True}

def perform_inspection(state: NeuroDiagnosticState):
    print(f'Checking diagnostic set components for {state["device_id"]}')
    return {'inspection_passed': True}

graph = StateGraph(NeuroDiagnosticState)
graph.add_node('compliance', validate_compliance)
graph.add_node('inspection', perform_inspection)
graph.add_edge('compliance', 'inspection')
graph.add_edge('inspection', END)
graph.set_entry_point('compliance')
graph = graph.compile()