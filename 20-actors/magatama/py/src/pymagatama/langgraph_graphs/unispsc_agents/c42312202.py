from typing import TypedDict
from langgraph.graph import StateGraph, END

class SuturingKitState(TypedDict):
    kit_id: str
    is_sterile: bool
    compliance_docs: list
    status: str

def validate_sterility(state: SuturingKitState):
    return {"status": "Validated" if state["is_sterile"] else "Rejected"}

def check_compliance(state: SuturingKitState):
    return {"compliance_docs": ["ISO_13485"]}

graph = StateGraph(SuturingKitState)
graph.add_node("validate", validate_sterility)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()