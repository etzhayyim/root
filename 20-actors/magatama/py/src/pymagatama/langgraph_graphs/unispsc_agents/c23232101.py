from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    part_id: str
    safety_check: bool
    compliance_verified: bool

def validate_part(state: RobotState):
    print(f"Validating part: {state['part_id']}")
    return {"safety_check": True}

def check_compliance(state: RobotState):
    print("Checking dual-use compliance export regulations.")
    return {"compliance_verified": True}

graph = StateGraph(RobotState)
graph.add_node("validate", validate_part)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()