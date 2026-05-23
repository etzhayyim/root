from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    material_spec: str
    tolerance: float
    inspection_passed: bool

def validate_material(state: ForgingState):
    print(f"Validating material: {state['material_spec']}")
    return {"inspection_passed": True}

def check_dimensions(state: ForgingState):
    print(f"Checking tolerances: {state['tolerance']}")
    return {"inspection_passed": state['tolerance'] < 0.05}

graph = StateGraph(ForgingState)
graph.add_node("validate", validate_material)
graph.add_node("check_dims", check_dimensions)
graph.add_edge("validate", "check_dims")
graph.add_edge("check_dims", END)
graph.set_entry_point("validate")
graph.compile()
