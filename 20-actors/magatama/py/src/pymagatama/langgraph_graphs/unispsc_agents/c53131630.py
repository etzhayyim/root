from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    product_name: str
    has_gmp: bool
    is_compliant: bool

def validate_ingredients(state: ProcessingState):
    print(f"Validating ingredients for {state['product_name']}...")
    return {"is_compliant": True}

def check_certification(state: ProcessingState):
    print("Verifying GMP certification...")
    return {"has_gmp": True}

graph = StateGraph(ProcessingState)
graph.add_node("validate", validate_ingredients)
graph.add_node("certify", check_certification)
graph.set_entry_point("validate")
graph.add_edge("validate", "certify")
graph.add_edge("certify", END)
graph = graph.compile()