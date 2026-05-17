from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    part_id: str
    spec_compliance: bool
    validation_logs: List[str]
    ready_for_procurement: bool

def validate_specs(state: RobotState) -> RobotState:
    # Logic for checking high-precision engineering specs
    logs = [f'Validating specs for {state["part_id"]}']
    return {**state, "spec_compliance": True, "validation_logs": logs}

def check_compliance(state: RobotState) -> RobotState:
    # Logic for dual-use export control checks
    return {**state, "ready_for_procurement": state["spec_compliance"]}

builder = StateGraph(RobotState)
builder.add_node("validate", validate_specs)
builder.add_node("compliance", check_compliance)
builder.add_edge("validate", "compliance")
builder.add_edge("compliance", END)
builder.set_entry_point("validate")
graph = builder.compile()