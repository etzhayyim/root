from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    part_id: str
    inspection_status: bool
    compliance_verified: bool

def validate_material(state: ProcurementState) -> dict:
    # Simulate titanium alloy spectroscopic analysis
    return {"compliance_verified": True}

    def run_inspection(state: ProcurementState) -> dict:
    # Simulate dimensional tolerance checking
    return {"inspection_status": True}

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_material)
graph.add_node("inspect", run_inspection)
graph.set_entry_point("validate")
graph.add_edge("validate", "inspect")
graph.add_edge("inspect", END)
graph = graph.compile()