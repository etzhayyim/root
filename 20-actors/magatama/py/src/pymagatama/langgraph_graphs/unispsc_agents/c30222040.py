from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TunnelState(TypedDict):
    project_id: str
    geological_data: dict
    structure_specs: List[str]
    validation_status: str

def validate_geology(state: TunnelState):
    return {"validation_status": "Geo-Check-Passed" if state["geological_data"] else "Failed"}

def verify_specs(state: TunnelState):
    return {"validation_status": "Specs-Verified"}

graph = StateGraph(TunnelState)
graph.add_node("validate_geology", validate_geology)
graph.add_node("verify_specs", verify_specs)
graph.set_entry_point("validate_geology")
graph.add_edge("validate_geology", "verify_specs")
graph.add_edge("verify_specs", END)
graph = graph.compile()
