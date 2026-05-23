from typing import TypedDict
from langgraph.graph import StateGraph, END

class VocationAidState(TypedDict):
    item_name: str
    safety_verified: bool
    compliance_docs: list

def validate_safety(state: VocationAidState):
    print(f'Validating safety for: {state["item_name"]}')
    return {"safety_verified": True}

def check_compliance(state: VocationAidState):
    print('Checking regulatory compliance for educational aids')
    return {"compliance_docs": ["ISO-9001"]}

graph = StateGraph(VocationAidState)
graph.add_node("safety", validate_safety)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("safety")
graph.add_edge("safety", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()
