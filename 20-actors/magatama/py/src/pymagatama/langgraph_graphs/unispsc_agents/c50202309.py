from typing import TypedDict
from langgraph.graph import StateGraph, END

class BeverageState(TypedDict):
    product_id: str
    quality_check: bool
    expiry_check: bool

def validate_ingredients(state: BeverageState):
    print(f"Validating ingredients for {state['product_id']}")
    return {"quality_check": True}

def check_shelf_life(state: BeverageState):
    print(f"Verifying shelf life for {state['product_id']}")
    return {"expiry_check": True}

graph = StateGraph(BeverageState)
graph.add_node("validate", validate_ingredients)
graph.add_node("expiry", check_shelf_life)
graph.set_entry_point("validate")
graph.add_edge("validate", "expiry")
graph.add_edge("expiry", END)
graph = graph.compile()