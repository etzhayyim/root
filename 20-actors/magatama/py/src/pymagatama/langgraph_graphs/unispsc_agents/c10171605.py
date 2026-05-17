from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class FertilizerState(TypedDict):
    commodity_id: str
    quality_metrics: dict
    approved: bool
    history: List[str]

def validate_quality(state: FertilizerState):
    metrics = state.get("quality_metrics", {})
    is_valid = metrics.get("moisture", 0) < 15 and metrics.get("purity", 0) > 95
    return {"approved": is_valid, "history": state["history"] + ["quality_validated"]}

def route_logistics(state: FertilizerState):
    return "approved" if state["approved"] else "rejected"

graph = StateGraph(FertilizerState)
graph.add_node("validate", validate_quality)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
app = graph.compile()