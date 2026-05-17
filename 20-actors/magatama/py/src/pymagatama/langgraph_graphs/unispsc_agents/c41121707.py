from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    item_name: str
    specs: dict
    validation_passed: bool
    compliance_status: List[str]

def validate_specs(state: ProcurementState):
    required = ['material_specification', 'sterile_certification']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed, 'compliance_status': ['Specs Verified'] if passed else ['Specs Incomplete']}

def approval_check(state: ProcurementState):
    return 'APPROVED' if state['validation_passed'] else 'REJECTED'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('approval', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
compiled_graph = graph.compile()