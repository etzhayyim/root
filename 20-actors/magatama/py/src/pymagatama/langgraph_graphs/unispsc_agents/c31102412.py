from langgraph.graph import StateGraph, END
from typing import TypedDict

class CastingState(TypedDict):
    material: str
    tolerance_check: bool
    validation_passed: bool

def check_material(state: CastingState):
    state["validation_passed"] = state["material"] == "Bronze"
    return state

def finalize_order(state: CastingState):
    return {"validation_passed": True}

graph = StateGraph(CastingState)
graph.add_node("check", check_material)
graph.add_node("finalize", finalize_order)
graph.set_entry_point("check")
graph.add_edge("check", "finalize")
graph.add_edge("finalize", END)
graph = graph.compile()
