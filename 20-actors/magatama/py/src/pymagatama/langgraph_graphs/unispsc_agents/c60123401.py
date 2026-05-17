from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CraftSupplyState(TypedDict):
    item_name: str
    diameter_mm: float
    has_safety_cert: bool
    validation_passed: bool

def validate_specs(state: CraftSupplyState):
    if state['diameter_mm'] > 0 and state['has_safety_cert']:
        return {"validation_passed": True}
    return {"validation_passed": False}

graph = StateGraph(CraftSupplyState)
graph.add_node("validate", validate_specs)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()