from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SteelSpec(TypedDict):
    material_grade: str
    diameter: float
    thickness: float
    compliance: bool

def validate_specs(state: SteelSpec):
    print(f"Validating grade: {state['material_grade']}")
    state['compliance'] = state['diameter'] > 0 and state['thickness'] > 0
    return state

def detect_export_risk(state: SteelSpec):
    print("Checking export controls...")
    return state

builder = StateGraph(SteelSpec)
builder.add_node("validate", validate_specs)
builder.add_node("export_check", detect_export_risk)
builder.set_entry_point("validate")
builder.add_edge("validate", "export_check")
builder.add_edge("export_check", END)
graph = builder.compile()