from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    batch_id: str
    purity_level: float
    validation_checks: List[str]
    is_compliant: bool

def validate_quality(state: ProcessingState) -> ProcessingState:
    state["validation_checks"].append("quality_check_passed")
    state["is_compliant"] = state["purity_level"] >= 0.99
    return state

def check_compliance(state: ProcessingState) -> ProcessingState:
    if state["is_compliant"]:
        state["validation_checks"].append("export_control_passed")
    return state

workflow = StateGraph(ProcessingState)
workflow.add_node("validate", validate_quality)
workflow.add_node("compliance", check_compliance)
workflow.add_edge("validate", "compliance")
workflow.add_edge("compliance", END)
workflow.set_entry_point("validate")
graph = workflow.compile()
