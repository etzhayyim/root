from typing import TypedDict
from langgraph.graph import StateGraph, END

class CoilProcurementState(TypedDict):
    material_spec: dict
    validation_passed: bool
    compliance_report: str

def validate_alloy_specs(state: CoilProcurementState):
    # Business logic for metallurgical standard validation
    grade = state['material_spec'].get('grade')
    is_valid = grade is not None and len(grade) > 0
    return {"validation_passed": is_valid}

def generate_compliance(state: CoilProcurementState):
    return {"compliance_report": "Standard compliant" if state['validation_passed'] else "Revision required"}

graph = StateGraph(CoilProcurementState)
graph.add_node("validate", validate_alloy_specs)
graph.add_node("compliance", generate_compliance)
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()