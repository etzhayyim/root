from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_id: str
    purity_check: bool
    compliance_docs: List[str]
    approved: bool

def validate_purity(state: ProcurementState):
    return {"purity_check": True}

def verify_compliance(state: ProcurementState):
    return {"approved": len(state['compliance_docs']) > 0}

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_purity)
graph.add_node("compliance", verify_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()