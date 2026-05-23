from typing import TypedDict
from langgraph.graph import StateGraph, END

class MorcellatorState(TypedDict):
    device_id: str
    is_sterile: bool
    validation_passed: bool

def validate_sterility(state: MorcellatorState):
    return {"validation_passed": state.get("is_sterile", False)}

def check_compliance(state: MorcellatorState):
    print(f"Checking regulatory compliance for ID: {state['device_id']}")
    return {"validation_passed": True}

graph = StateGraph(MorcellatorState)
graph.add_node("validate", validate_sterility)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()
