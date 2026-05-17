from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MetalPowderState(TypedDict):
    material_id: str
    composition_check: bool
    safety_clearance: bool
    quality_score: float
    steps: List[str]

def validate_composition(state: MetalPowderState):
    # Simulate spectroscopic analysis for metal purity
    print(f"Validating composition for {state['material_id']}")
    return {"composition_check": True, "steps": state.get("steps", []) + ["composition_verified"]}

def perform_safety_check(state: MetalPowderState):
    # Dangerous goods verification
    print(f"Performing safety/dual-use check for {state['material_id']}")
    return {"safety_clearance": True, "steps": state.get("steps", []) + ["safety_verified"]}

builder = StateGraph(MetalPowderState)
builder.add_node("validate_composition", validate_composition)
builder.add_node("perform_safety_check", perform_safety_check)
builder.set_entry_point("validate_composition")
builder.add_edge("validate_composition", "perform_safety_check")
builder.add_edge("perform_safety_check", END)

graph = builder.compile()