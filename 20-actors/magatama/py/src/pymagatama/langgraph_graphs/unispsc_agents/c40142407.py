from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlangeState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_status: str

def validate_specs(state: FlangeState):
    # Business logic for industrial standard verification
    required = ['pressure_rating', 'material_grade', 'bolt_circle_diameter']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed, 'compliance_status': 'COMPLIANT' if passed else 'REJECTED'}

graph = StateGraph(FlangeState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()