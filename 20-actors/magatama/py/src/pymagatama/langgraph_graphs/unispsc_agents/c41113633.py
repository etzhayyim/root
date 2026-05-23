from typing import TypedDict
from langgraph.graph import StateGraph, END

class PotentiometerState(TypedDict):
    spec: dict
    validation_passed: bool
    compliance_status: str

def validate_specs(state: PotentiometerState):
    required = ['resistance', 'tolerance']
    passed = all(k in state['spec'] for k in required)
    return {'validation_passed': passed, 'compliance_status': 'COMPLIANT' if passed else 'INCOMPLETE'}

def export_check(state: PotentiometerState):
    if state.get('spec', {}).get('precision', False):
        return {'compliance_status': 'DUAL_USE_REVIEW_REQUIRED'}
    return {'compliance_status': 'PASSED'}

graph = StateGraph(PotentiometerState)
graph.add_node('validate', validate_specs)
graph.add_node('export_review', export_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_review')
graph.add_edge('export_review', END)
graph = graph.compile()
