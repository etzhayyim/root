from typing import TypedDict
from langgraph.graph import StateGraph, END

class PaintState(TypedDict):
    paint_type: str
    viscosity_ok: bool
    safety_verified: bool

def validate_viscosity(state: PaintState):
    return {"viscosity_ok": state["paint_type"] == "acrylic_airbrush"}

def verify_safety(state: PaintState):
    return {"safety_verified": True}

graph = StateGraph(PaintState)
graph.add_node("validate_viscosity", validate_viscosity)
graph.add_node("verify_safety", verify_safety)
graph.set_entry_point("validate_viscosity")
graph.add_edge("validate_viscosity", "verify_safety")
graph.add_edge("verify_safety", END)
graph = graph.compile()
