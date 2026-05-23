from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    commodity_id: str
    purity_check_passed: bool
    safety_clearance: bool
    hazmat_approved: bool
    history: List[str]

def validate_purity(state: ChemicalProcurementState):
    # Simulate chemical analysis logic
    return {"purity_check_passed": True, "history": state["history"] + ["Purity validated"]}

def perform_safety_check(state: ChemicalProcurementState):
    # Simulate regulatory safety assessment
    return {"safety_clearance": True, "history": state["history"] + ["Safety clearance passed"]}

def hazmat_logistics_review(state: ChemicalProcurementState):
    # Simulate dangerous goods compliance verification
    return {"hazmat_approved": True, "history": state["history"] + ["Hazmat logistics approved"]}

graph = StateGraph(ChemicalProcurementState)
graph.add_node("validate_purity", validate_purity)
graph.add_node("safety_check", perform_safety_check)
graph.add_node("hazmat_review", hazmat_logistics_review)

graph.set_entry_point("validate_purity")
graph.add_edge("validate_purity", "safety_check")
graph.add_edge("safety_check", "hazmat_review")
graph.add_edge("hazmat_review", END)

graph = graph.compile()
