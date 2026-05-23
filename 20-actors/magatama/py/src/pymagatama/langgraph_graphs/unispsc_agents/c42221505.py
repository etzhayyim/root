from typing import TypedDict
from langgraph.graph import StateGraph, END

class CatheterState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_status: str

def validate_medical_spec(state: CatheterState):
    fields = ['gauge_size', 'sterilization_method']
    passed = all(k in state['spec_data'] for k in fields)
    return {'validation_passed': passed}

def check_compliance(state: CatheterState):
    status = 'APPROVED' if state['validation_passed'] else 'REJECTED'
    return {'compliance_status': status}

graph = StateGraph(CatheterState)
graph.add_node('validate', validate_medical_spec)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
