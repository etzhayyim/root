from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    compliance_docs: list
    authorized: bool

def validate_purity(state: ProcurementState):
    return {"authorized": state["purity"] >= 99.5}

def check_compliance(state: ProcurementState):
    return {"authorized": len(state["compliance_docs"]) >= 3}

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_purity)
graph.add_node("compliance", check_compliance)
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph.set_entry_point("validate")
graph = graph.compile()