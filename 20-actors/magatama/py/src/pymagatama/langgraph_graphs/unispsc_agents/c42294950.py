from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    tool_id: str
    quality_check_passed: bool
    sterilization_validated: bool

def validate_tool_integrity(state: ToolState) -> ToolState:
    print(f'Validating integrity of tool: {state["tool_id"]}')
    return {**state, "quality_check_passed": True}

def verify_sterilization(state: ToolState) -> ToolState:
    print(f'Verifying sterilization logs for: {state["tool_id"]}')
    return {**state, "sterilization_validated": True}

graph = StateGraph(ToolState)
graph.add_node("integrity_check", validate_tool_integrity)
graph.add_node("sterilization_check", verify_sterilization)
graph.set_entry_point("integrity_check")
graph.add_edge("integrity_check", "sterilization_check")
graph.add_edge("sterilization_check", END)
compiled_graph = graph.compile()