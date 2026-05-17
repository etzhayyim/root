from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class AdhesiveState(TypedDict):
    material_id: str
    spec_sheet_verified: bool
    safety_score: float
    compliance_tags: List[str]

def validate_spec(state: AdhesiveState) -> AdhesiveState:
    if not state.get("spec_sheet_verified", False):
        state["compliance_tags"].append("REJECTED_MISSING_SDS")
    return state

def evaluate_safety(state: AdhesiveState) -> AdhesiveState:
    if state.get("safety_score", 0) < 0.7:
        state["compliance_tags"].append("RISK_HIGH")
    return state

graph = StateGraph(AdhesiveState)
graph.add_node("validate", validate_spec)
graph.add_node("safety", evaluate_safety)
graph.add_edge("validate", "safety")
graph.add_edge("safety", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()