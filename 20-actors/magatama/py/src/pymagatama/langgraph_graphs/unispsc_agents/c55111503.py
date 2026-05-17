from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    license_type: str
    user_count: int
    compliance_status: bool

def validate_license(state: ProcurementState):
    state['compliance_status'] = state['user_count'] > 0
    return state

def approve_procurement(state: ProcurementState):
    return {"status": "approved"}

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_license)
graph.add_node("approve", approve_procurement)
graph.add_edge("validate", "approve")
graph.add_edge("approve", END)
graph.set_entry_point("validate")
graph = graph.compile()