from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrawingState(TypedDict):
    file_path: str
    is_compliant: bool
    revision_verified: bool

def validate_drawing(state: DrawingState):
    # Simulate parsing CAD metadata
    print(f"Validating drawing: {state['file_path']}")
    return {"is_compliant": True}

def check_revision(state: DrawingState):
    return {"revision_verified": True}

graph = StateGraph(DrawingState)
graph.add_node("validate", validate_drawing)
graph.add_node("check_rev", check_revision)
graph.add_edge("validate", "check_rev")
graph.add_edge("check_rev", END)
graph.set_entry_point("validate")
graph = graph.compile()