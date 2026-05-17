from typing import TypedDict
from langgraph.graph import StateGraph, END

class PostmortemToolState(TypedDict):
    tool_id: str
    inspection_passed: bool
    sterilization_ok: bool

def validate_tool_integrity(state: PostmortemToolState):
    print(f"Validating integrity for: {state['tool_id']}")
    return {"inspection_passed": True}

def check_compliance(state: PostmortemToolState):
    print("Checking sterilization compliance...")
    return {"sterilization_ok": True}

graph = StateGraph(PostmortemToolState)
graph.add_node("integrity_check", validate_tool_integrity)
graph.add_node("compliance_check", check_compliance)
graph.set_entry_point("integrity_check")
graph.add_edge("integrity_check", "compliance_check")
graph.add_edge("compliance_check", END)
graph = graph.compile()