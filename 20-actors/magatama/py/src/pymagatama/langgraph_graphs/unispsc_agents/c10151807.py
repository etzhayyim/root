from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class CattleState(TypedDict):
    cattle_id: str
    health_status: str
    inspection_results: list[str]
    is_compliant: bool

def validate_health(state: CattleState) -> dict:
    # Logic to verify health status against vet records
    status = "Healthy" if "pass" in state["inspection_results"] else "Quarantine"
    return {"health_status": status, "is_compliant": status == "Healthy"}

def update_traceability(state: CattleState) -> dict:
    return {"inspection_results": state["inspection_results"] + ["Traceability Updated"]}

builder = StateGraph(CattleState)
builder.add_node("health_check", validate_health)
builder.add_node("traceability", update_traceability)
builder.set_entry_point("health_check")
builder.add_edge("health_check", "traceability")
builder.add_edge("traceability", END)
graph = builder.compile()