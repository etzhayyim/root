from typing import TypedDict
from langgraph.graph import StateGraph, END

class ClothProcessState(TypedDict):
    material: str
    dimensions: str
    is_validated: bool

def validate_specs(state: ClothProcessState):
    # Business logic for confirming non-abrasive material
    state['is_validated'] = 'microfiber' in state['material'].lower()
    return state

def finalize_order(state: ClothProcessState):
    return {"status": "READY_FOR_PURCHASE"}

graph = StateGraph(ClothProcessState)
graph.add_node("validate", validate_specs)
graph.add_node("finalize", finalize_order)
graph.set_entry_point("validate")
graph.add_edge("validate", "finalize")
graph.add_edge("finalize", END)
graph = graph.compile()
