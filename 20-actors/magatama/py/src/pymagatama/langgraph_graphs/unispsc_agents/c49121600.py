from typing import TypedDict
from langgraph.graph import StateGraph, END

class CampingFurnitureState(TypedDict):
    material: str
    weight_capacity: int
    is_compliant: bool

def validate_specs(state: CampingFurnitureState):
    state["is_compliant"] = state["weight_capacity"] > 0 and bool(state["material"])
    return state

graph = StateGraph(CampingFurnitureState)
graph.add_node("validate", validate_specs)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()