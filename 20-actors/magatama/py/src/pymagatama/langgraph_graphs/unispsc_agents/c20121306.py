from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class RobotEndEffectorState(TypedDict):
    spec_requirements: dict
    validation_results: Annotated[list, operator.add]
    is_approved: bool

def validate_payload(state: RobotEndEffectorState):
    payload = state['spec_requirements'].get('payload_capacity_kg', 0)
    result = "Payload validation passed" if payload > 0 else "Payload validation failed"
    return {'validation_results': [result]}

def check_safety_compliance(state: RobotEndEffectorState):
    compliant = state['spec_requirements'].get('iso_compliance_cert', False)
    result = "Safety compliance verified" if compliant else "Safety compliance missing"
    return {'validation_results': [result]}

builder = StateGraph(RobotEndEffectorState)
builder.add_node("validate_payload", validate_payload)
builder.add_node("check_safety_compliance", check_safety_compliance)
builder.set_entry_point("validate_payload")
builder.add_edge("validate_payload", "check_safety_compliance")
builder.add_edge("check_safety_compliance", END)
graph = builder.compile()