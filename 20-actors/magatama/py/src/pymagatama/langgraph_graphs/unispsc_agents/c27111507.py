from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolSpecState(TypedDict):
    tool_type: str
    material_hrc: float
    specs_verified: bool

def validate_specs(state: ToolSpecState):
    state['specs_verified'] = state['material_hrc'] >= 50
    return state

def approve_procurement(state: ToolSpecState):
    return {"status": "APPROVED" if state['specs_verified'] else "REJECTED"}

graph = StateGraph(ToolSpecState)
graph.add_node("validate", validate_specs)
graph.add_node("approve", approve_procurement)
graph.add_edge("validate", "approve")
graph.add_edge("approve", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()