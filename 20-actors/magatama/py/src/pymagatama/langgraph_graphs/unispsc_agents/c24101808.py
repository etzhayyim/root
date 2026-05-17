from typing import TypedDict
from langgraph.graph import StateGraph, END

class WheelChockState(TypedDict):
    material: str
    weight_capacity: float
    safety_compliant: bool

def validate_materials(state: WheelChockState):
    return {"safety_compliant": state["material"] in ["Rubber", "Polyurethane", "Aluminum"]}

def approve_procurement(state: WheelChockState):
    return {"safety_compliant": True}

graph = StateGraph(WheelChockState)
graph.add_node("validate", validate_materials)
graph.add_node("approve", approve_procurement)
graph.add_edge("validate", "approve")
graph.add_edge("approve", END)
graph.set_entry_point("validate")
graph = graph.compile()