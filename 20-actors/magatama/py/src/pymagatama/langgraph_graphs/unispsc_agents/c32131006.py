from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ICComponentState(TypedDict):
    part_number: str
    spec_data: dict
    validation_passed: bool
    compliance_status: List[str]

def validate_specs(state: ICComponentState):
    specs = state['spec_data']
    passed = 'pitch_spacing_mm' in specs and 'pin_count' in specs
    return {'validation_passed': passed}

def check_compliance(state: ICComponentState):
    return {'compliance_status': ['RoHS_Verified'] if state['validation_passed'] else ['Pending_Review']}

graph = StateGraph(ICComponentState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
