from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StentProcurementState(TypedDict):
    order_id: str
    specifications: dict
    compliance_cleared: bool
    shipping_status: str

def validate_medical_specs(state: StentProcurementState):
    # Business logic for Coronary Stent medical device validation
    if "ISO 13485" not in state["specifications"].get("certs", []):
        return {"compliance_cleared": False}
    return {"compliance_cleared": True}

def route_by_compliance(state: StentProcurementState):
    return "process" if state["compliance_cleared"] else "reject"

graph = StateGraph(StentProcurementState)
graph.add_node("validate", validate_medical_specs)
graph.set_entry_point("validate")
graph.add_conditional_edges("validate", route_by_compliance, {"process": "process", "reject": END})
graph.add_node("process", lambda s: {"shipping_status": "Ready for cold chain"})
graph.add_edge("process", END)
graph = graph.compile()