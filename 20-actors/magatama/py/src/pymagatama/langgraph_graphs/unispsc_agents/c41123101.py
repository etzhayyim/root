from typing import TypedDict
from langgraph.graph import StateGraph, END

class DialysisState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_medical_grade(state: DialysisState):
    fields = ['MWCO', 'sterilization', 'bio_cert']
    passed = all(field in state['spec_data'] for field in fields)
    return {'validation_passed': passed, 'compliance_report': 'Verified' if passed else 'Missing Specs'}

def approval_node(state: DialysisState):
    return {'compliance_report': 'Ready for Procurement' if state['validation_passed'] else 'Rejected'}

graph = StateGraph(DialysisState)
graph.add_node('validate', validate_medical_grade)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()