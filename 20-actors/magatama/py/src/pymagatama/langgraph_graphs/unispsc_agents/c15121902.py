from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class WeldingSupplyState(TypedDict):
    material_code: str
    spec_compliance: bool
    safety_check_passed: bool
    inspection_steps: Annotated[List[str], operator.add]

def validate_material_spec(state: WeldingSupplyState):
    print(f"Validating metallurgy for {state['material_code']}")
    return {"spec_compliance": True, "inspection_steps": ["chemical_analysis_complete"]}

def perform_safety_risk_check(state: WeldingSupplyState):
    print("Running export and hazard control checks")
    return {"safety_check_passed": True, "inspection_steps": ["dual_use_clearance"]}

builder = StateGraph(WeldingSupplyState)
builder.add_node("validate", validate_material_spec)
builder.add_node("safety", perform_safety_risk_check)
builder.set_entry_point("validate")
builder.add_edge("validate", "safety")
builder.add_edge("safety", END)
graph = builder.compile()
