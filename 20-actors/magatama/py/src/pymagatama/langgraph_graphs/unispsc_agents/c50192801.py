from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FoodState(TypedDict):
    product_name: str
    expiry_date: str
    temperature_check: bool
    approved: bool

def validate_perishables(state: FoodState):
    # Simulate cold chain validation logic
    is_valid = state['temperature_check'] == True
    return {"approved": is_valid}

workflow = StateGraph(FoodState)
workflow.add_node("validate", validate_perishables)
workflow.set_entry_point("validate")
workflow.add_edge("validate", END)
graph = workflow.compile()