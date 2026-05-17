from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_status: str

def validate_specs(state: ExtrusionState):
    required = ['material_grade', 'tolerance']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed, 'compliance_status': 'VALIDATED' if passed else 'REJECTED'}

workflow = StateGraph(ExtrusionState)
workflow.add_node('validation', validate_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()