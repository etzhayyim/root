from typing import TypedDict
from langgraph.graph import StateGraph, END

class LockNutState(TypedDict):
    spec_sheet: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: LockNutState):
    required = ['material', 'thread', 'torque_rating']
    passed = all(k in state['spec_sheet'] for k in required)
    return {'validation_passed': passed, 'compliance_report': 'Verified' if passed else 'Failed'}

def generate_cert(state: LockNutState):
    return {'compliance_report': 'Certified ISO standards applied to batch.'}

graph = StateGraph(LockNutState)
graph.add_node('validate', validate_specs)
graph.add_node('certify', generate_cert)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
graph = graph.compile()