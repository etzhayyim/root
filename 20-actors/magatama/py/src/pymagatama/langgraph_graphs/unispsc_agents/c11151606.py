from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class AlloyState(TypedDict):
    purity: float
    strength: float
    compliant: bool
    logs: List[str]

def analyze_ingot(state: AlloyState) -> AlloyState:
    logs = state.get("logs", [])
    is_compliant = state["purity"] >= 99.9 and state["strength"] >= 450.0
    logs.append(f"Analysis complete: Compliant={is_compliant}")
    return {"compliant": is_compliant, "logs": logs}

def validate_certification(state: AlloyState) -> AlloyState:
    logs = state.get("logs", [])
    logs.append("Checking mill test certificate...")
    return {"logs": logs}

workflow = StateGraph(AlloyState)
workflow.add_node("analyze", analyze_ingot)
workflow.add_node("certify", validate_certification)
workflow.set_entry_point("analyze")
workflow.add_edge("analyze", "certify")
workflow.add_edge("certify", END)

graph = workflow.compile()