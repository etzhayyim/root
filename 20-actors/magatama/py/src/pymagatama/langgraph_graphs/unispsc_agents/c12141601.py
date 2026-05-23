from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    batch_id: str
    purity_level: float
    safety_verified: bool
    compliance_tags: List[str]

def validate_purity(state: ChemicalState):
    return {"safety_verified": state["purity_level"] >= 0.99}

def check_compliance(state: ChemicalState):
    tags = ["HAZMAT_CHECK"] if state["safety_verified"] else ["RESTRICTED_ACCESS"]
    return {"compliance_tags": tags}

graph = StateGraph(ChemicalState)
graph.add_node("validate", validate_purity)
graph.add_node("compliance", check_compliance)
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph.set_entry_point("validate")
graph = graph.compile()
