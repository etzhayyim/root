from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_name: str
    compliance_cleared: bool
    purity_level: float

def validate_gmp(state: ProcurementState):
    print(f"Verifying GMP for {state['product_name']}...")
    return {"compliance_cleared": True}

def check_purity(state: ProcurementState):
    is_ok = state['purity_level'] >= 99.0
    return {"compliance_cleared": is_ok}

graph = StateGraph(ProcurementState)
graph.add_node("validate_gmp", validate_gmp)
graph.add_node("check_purity", check_purity)
graph.set_entry_point("validate_gmp")
graph.add_edge("validate_gmp", "check_purity")
graph.add_edge("check_purity", END)
graph = graph.compile()