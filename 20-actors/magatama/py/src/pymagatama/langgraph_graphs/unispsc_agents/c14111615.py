from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PaperProcurementState(TypedDict):
    paper_code: str
    quality_metrics: dict
    approved: bool
    history: List[str]

def validate_quality(state: PaperProcurementState) -> PaperProcurementState:
    metrics = state.get("quality_metrics", {})
    # Logic: Validate GSM and Brightness thresholds
    is_valid = metrics.get("basis_weight", 0) >= 80 and metrics.get("brightness", 0) >= 90
    state["approved"] = is_valid
    state["history"].append(f"Quality validation result: {is_valid}")
    return state

def route_procurement(state: PaperProcurementState) -> str:
    return "end" if state["approved"] else "error"

builder = StateGraph(PaperProcurementState)
builder.add_node("validate", validate_quality)
builder.add_edge("validate", END)
builder.set_entry_point("validate")
graph = builder.compile()