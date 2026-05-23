from langgraph.graph import StateGraph, END
from typing import TypedDict

class ProcurementState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_stainless_specs(state: ProcurementState):
    required = ['grade', 'tolerance', 'finish']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed, 'compliance_report': 'Success' if passed else 'Missing Specs'}

def generate_rfq_workflow():
    graph = StateGraph(ProcurementState)
    graph.add_node('validate', validate_stainless_specs)
    graph.set_entry_point('validate')
    graph.add_edge('validate', END)
    return graph.compile()

graph = generate_rfq_workflow()
