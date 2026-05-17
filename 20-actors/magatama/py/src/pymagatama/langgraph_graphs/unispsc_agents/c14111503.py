from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END

class StationeryState(TypedDict):
    spec_data: dict
    validation_results: list[str]
    approved: bool

def validate_specs(state: StationeryState):
    fields = ["dimensions_mm", "adhesive_grade", "paper_weight_gsm"]
    missing = [f for f in fields if f not in state["spec_data"]]
    return {"validation_results": [f"Missing: {f}" for f in missing], "approved": len(missing) == 0}

def route_procurement(state: StationeryState):
    return "approved" if state["approved"] else END

graph = StateGraph(StationeryState)
graph.add_node("validate", validate_specs)
graph.add_edge("validate", END)
graph.set_entry_point("validate")
graph = graph.compile()