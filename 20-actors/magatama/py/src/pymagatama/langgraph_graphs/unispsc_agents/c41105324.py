from typing import TypedDict
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    sequence_data: str
    purity_check: bool
    temp_log_verified: bool

def validate_sequence(state: ReagentState):
    return {"purity_check": len(state["sequence_data"]) > 0}

def verify_storage(state: ReagentState):
    return {"temp_log_verified": True}

graph = StateGraph(ReagentState)
graph.add_node("validate", validate_sequence)
graph.add_node("storage_check", verify_storage)
graph.add_edge("validate", "storage_check")
graph.add_edge("storage_check", END)
graph.set_entry_point("validate")
graph = graph.compile()