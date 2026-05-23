from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SwabState(TypedDict):
    material_type: str
    is_sterile: bool
    compliance_docs: List[str]
    validation_passed: bool

def validate_specs(state: SwabState):
    passed = state['is_sterile'] and 'ISO_Certificate' in state['compliance_docs']
    return {'validation_passed': passed}

def check_compliance(state: SwabState):
    return 'COMPLIANT' if state['validation_passed'] else 'REJECTED'

graph = StateGraph(SwabState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
