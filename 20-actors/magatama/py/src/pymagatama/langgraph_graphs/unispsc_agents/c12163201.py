from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END

class SemiconductorMaterialState(TypedDict):
    material_code: str
    purity_level: float
    process_compatibility_passed: bool
    safety_check_passed: bool
    validation_logs: List[str]

def validate_material_purity(state: SemiconductorMaterialState):
    # Simulate purity check
    purity = state.get("purity_level", 0.0)
    if purity >= 99.999:
        return {"validation_logs": state["validation_logs"] + ["Purity check passed (Ultra-High Purity)"]}
    return {"validation_logs": state["validation_logs"] + ["Purity check failed"]}

def check_safety_protocols(state: SemiconductorMaterialState):
    # Simulate hazard mitigation check
    return {"safety_check_passed": True, "validation_logs": state["validation_logs"] + ["Safety protocols verified for hazardous gas"]}

def compile_graph():
    workflow = StateGraph(SemiconductorMaterialState)
    workflow.add_node("validate_purity", validate_material_purity)
    workflow.add_node("check_safety", check_safety_protocols)
    workflow.set_entry_point("validate_purity")
    workflow.add_edge("validate_purity", "check_safety")
    workflow.add_edge("check_safety", END)
    return workflow.compile()

graph = compile_graph()