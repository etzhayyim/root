from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LabKitState(TypedDict):
    kit_id: str
    expiry_check: bool
    compliance_passed: bool

def validate_expiry(state: LabKitState) -> LabKitState:
    print(f'Validating expiry for {state["kit_id"]}')
    return {"expiry_check": True}

def check_compliance(state: LabKitState) -> LabKitState:
    print(f'Verifying regulatory compliance for {state["kit_id"]}')
    return {"compliance_passed": True}

graph = StateGraph(LabKitState)
graph.add_node("expiry", validate_expiry)
graph.add_node("compliance", check_compliance)
graph.add_edge("expiry", "compliance")
graph.add_edge("compliance", END)
graph.set_entry_point("expiry")
app = graph.compile()
