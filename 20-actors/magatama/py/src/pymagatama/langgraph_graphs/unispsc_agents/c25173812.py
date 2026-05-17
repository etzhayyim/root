from typing import TypedDict
from langgraph.graph import StateGraph, END

class TransmissionState(TypedDict):
    part_number: str
    spec_verified: bool
    compliance_ok: bool

def validate_specs(state: TransmissionState):
    # Simulate gear ratio and torque validation logic
    print(f"Validating specs for {state['part_number']}")
    return {"spec_verified": True}

def check_compliance(state: TransmissionState):
    # Simulate dual-use export control check
    return {"compliance_ok": True}

graph = StateGraph(TransmissionState)
graph.add_node("validate", validate_specs)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()