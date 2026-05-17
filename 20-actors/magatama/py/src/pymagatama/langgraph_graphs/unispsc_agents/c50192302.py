from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoodProcurementState(TypedDict):
    product_name: str
    expiry_check: bool
    allergen_verified: bool
    approved_supplier: bool

def validate_food_safety(state: FoodProcurementState):
    print(f"Validating safety for {state['product_name']}")
    return {"expiry_check": True, "allergen_verified": True}

def verify_supplier(state: FoodProcurementState):
    return {"approved_supplier": True}

graph = StateGraph(FoodProcurementState)
graph.add_node("safety_check", validate_food_safety)
graph.add_node("supplier_verification", verify_supplier)
graph.set_entry_point("safety_check")
graph.add_edge("safety_check", "supplier_verification")
graph.add_edge("supplier_verification", END)
app = graph.compile()