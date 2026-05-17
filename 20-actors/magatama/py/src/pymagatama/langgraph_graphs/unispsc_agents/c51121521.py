from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_data: str
    compliance_ok: bool
    final_approval: bool

def validate_purity(state: ProcurementState):
    return {"compliance_ok": float(state['purity_data']) >= 99.0}

def approve_procurement(state: ProcurementState):
    return {"final_approval": state['compliance_ok']}

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_purity)
graph.add_node("approve", approve_procurement)
graph.set_entry_point("validate")
graph.add_edge("validate", "approve")
graph.add_edge("approve", END)
graph = graph.compile()