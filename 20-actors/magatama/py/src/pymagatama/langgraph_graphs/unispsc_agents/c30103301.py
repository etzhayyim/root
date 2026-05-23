from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BilletState(TypedDict):
    alloy_grade: str
    purity_level: float
    certification_docs: List[str]
    is_approved: bool

def validate_material(state: BilletState):
    # Business logic for alloy validation and certification check
    is_compliant = state['purity_level'] >= 99.5 and len(state['certification_docs']) > 0
    return {"is_approved": is_compliant}

workflow = StateGraph(BilletState)
workflow.add_node("validate", validate_material)
workflow.set_entry_point("validate")
workflow.add_edge("validate", END)
graph = workflow.compile()
