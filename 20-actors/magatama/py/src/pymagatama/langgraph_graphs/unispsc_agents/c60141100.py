from typing import TypedDict
from langgraph.graph import StateGraph, END

class GameProcurementState(TypedDict):
    product_name: str
    safety_verified: bool
    compliance_score: float

def validate_safety(state: GameProcurementState):
    print(f'Validating safety for: {state["product_name"]}')
    return {"safety_verified": True}

def check_compliance(state: GameProcurementState):
    return {"compliance_score": 95.0}

graph = StateGraph(GameProcurementState)
graph.add_node("safety", validate_safety)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("safety")
graph.add_edge("safety", "compliance")
graph.add_edge("compliance", END)
app = graph.compile()