from typing import TypedDict
from langgraph.graph import StateGraph, END

class GameState(TypedDict):
    product_id: str
    compliance_passed: bool
    shipping_ready: bool

def validate_safety(state: GameState):
    # Simulate safety check logic for board games
    print(f'Validating safety for {state["product_id"]}')
    return {"compliance_passed": True}

def process_logistics(state: GameState):
    print(f'Processing logistics for {state["product_id"]}')
    return {"shipping_ready": True}

graph = StateGraph(GameState)
graph.add_node("safety_check", validate_safety)
graph.add_node("logistics", process_logistics)
graph.set_entry_point("safety_check")
graph.add_edge("safety_check", "logistics")
graph.add_edge("logistics", END)
graph = graph.compile()
