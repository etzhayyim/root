from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ScreenProcurementState(TypedDict):
    dimensions: dict
    material_spec: str
    compliance_passed: bool
    validation_logs: List[str]

def validate_specs(state: ScreenProcurementState):
    # Simulate CAD dimension validation logic
    is_valid = all(v > 0 for v in state['dimensions'].values())
    return {"compliance_passed": is_valid, "validation_logs": ["Dimensions checked successfully"]}

def process_procurement(state: ScreenProcurementState):
    return {"validation_logs": state['validation_logs'] + ["Order routed to furniture logistics"]}

graph = StateGraph(ScreenProcurementState)
graph.add_node("validate", validate_specs)
graph.add_node("route", process_procurement)
graph.set_entry_point("validate")
graph.add_edge("validate", "route")
graph.add_edge("route", END)
graph = graph.compile()
