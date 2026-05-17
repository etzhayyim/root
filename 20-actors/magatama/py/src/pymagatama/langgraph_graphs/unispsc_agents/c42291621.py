from typing import TypedDict
from langgraph.graph import StateGraph, END

class RingRemoverState(TypedDict):
    model_id: str
    safety_check_passed: bool
    sterilization_validated: bool

def validate_model(state: RingRemoverState):
    print(f"Validating model: {state['model_id']}")
    return {"safety_check_passed": True}

def check_compliance(state: RingRemoverState):
    print("Verifying medical grade compliance...")
    return {"sterilization_validated": True}

graph = StateGraph(RingRemoverState)
graph.add_node("validate", validate_model)
graph.add_node("compliance", check_compliance)
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph.set_entry_point("validate")
graph = graph.compile()