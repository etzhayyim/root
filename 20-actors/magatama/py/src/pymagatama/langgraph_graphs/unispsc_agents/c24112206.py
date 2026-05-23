from typing import TypedDict
from langgraph.graph import StateGraph, END

class ContainerState(TypedDict):
    capacity: float
    material_certified: bool
    un_approved: bool

def validate_capacity(state: ContainerState):
    return {"capacity_valid": state["capacity"] > 0}

def check_compliance(state: ContainerState):
    compliance = state["material_certified"] and state["un_approved"]
    return {"compliant": compliance}

graph = StateGraph(ContainerState)
graph.add_node("validate", validate_capacity)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()
