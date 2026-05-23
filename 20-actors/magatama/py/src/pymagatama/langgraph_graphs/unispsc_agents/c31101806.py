from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_risk: str

def validate_casting_spec(state: CastState):
    required = ['alloy_grade', 'tolerance', 'testing_cert']
    passed = all(k in state['spec_data'] for k in required)
    return {"validation_passed": passed, "compliance_risk": "low" if passed else "high"}

def check_export_controls(state: CastState):
    # Dual-use check logic
    return {"compliance_risk": "restricted" if state['spec_data'].get('aerospace_grade') else "standard"}

graph = StateGraph(CastState)
graph.add_node("validate", validate_casting_spec)
graph.add_node("compliance", check_export_controls)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()
