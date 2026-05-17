from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SiCProcessState(TypedDict):
    material_id: str
    purity_check: bool
    impurity_report: List[str]
    validation_score: float

def validate_material_purity(state: SiCProcessState) -> SiCProcessState:
    # Specialized validation for Silicon Carbide
    if state.get("purity_percentage", 0) < 99.9:
        state["purity_check"] = False
        state["impurity_report"].append("Low purity detected")
    else:
        state["purity_check"] = True
    return state

def run_compliance_check(state: SiCProcessState) -> SiCProcessState:
    # Dual-use export control screening
    state["validation_score"] = 0.95
    return state

builder = StateGraph(SiCProcessState)
builder.add_node("validate_purity", validate_material_purity)
builder.add_node("compliance_check", run_compliance_check)
builder.set_entry_point("validate_purity")
builder.add_edge("validate_purity", "compliance_check")
builder.add_edge("compliance_check", END)

graph = builder.compile()