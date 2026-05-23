from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    drug_name: str
    purity_level: float
    requires_cold_chain: bool
    is_compliant: bool

def validate_purity(state: ProcurementState):
    return {"is_compliant": state["purity_level"] >= 0.99}

def check_certification(state: ProcurementState):
    return {"is_compliant": state["is_compliant"]}

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_purity)
graph.add_node("certify", check_certification)
graph.add_edge("validate", "certify")
graph.add_edge("certify", END)
graph.set_entry_point("validate")
graph = graph.compile()
