from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_medical_standards(state: ProcurementState):
    checks = ['ISO_13485', 'IEC_60601']
    passed = all(k in state['spec_data'] for k in checks)
    return {'validation_passed': passed, 'compliance_report': 'Standards verified' if passed else 'Missing certs'}

def approval_step(state: ProcurementState):
    return {'compliance_report': 'Approved for procurement' if state['validation_passed'] else 'Rejected'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_medical_standards)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
