from typing import TypedDict
from langgraph.graph import StateGraph, END

class LimeState(TypedDict):
    purity: float
    has_sds: bool
    is_compliant: bool

def validate_purity(state: LimeState):
    return {"is_compliant": state["purity"] >= 0.90 and state["has_sds"]}

workflow = StateGraph(LimeState)
workflow.add_node("validate", validate_purity)
workflow.set_entry_point("validate")
workflow.add_edge("validate", END)
graph = workflow.compile()
