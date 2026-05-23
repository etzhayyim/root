from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_level: float
    gmp_certified: bool
    compliance_cleared: bool

def validate_purity(state: ProcurementState):
    return {"compliance_cleared": state["purity_level"] >= 99.0 and state["gmp_certified"]}

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_purity)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()
