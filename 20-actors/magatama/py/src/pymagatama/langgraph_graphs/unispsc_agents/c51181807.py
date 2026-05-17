from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    gmp_certified: bool
    temp_compliant: bool

def validate_purity(state: ProcurementState):
    return {"purity_status": state["purity"] >= 99.0}

def check_compliance(state: ProcurementState):
    return {"compliant": state["gmp_certified"] and state["temp_compliant"]}

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_purity)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
compiled_graph = graph.compile()