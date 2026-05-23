from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoodSupplyState(TypedDict):
    temp_celsius: float
    haccp_verified: bool
    is_expired: bool

def validate_temp(state: FoodSupplyState):
    return {"status": "safe" if -25 <= state['temp_celsius'] <= -18 else "unsafe"}

def safety_check(state: FoodSupplyState):
    return "ok" if state['haccp_verified'] and not state['is_expired'] else "rejected"

graph = StateGraph(FoodSupplyState)
graph.add_node("validate_temp", validate_temp)
graph.add_node("safety_check", safety_check)
graph.set_entry_point("validate_temp")
graph.add_edge("validate_temp", "safety_check")
graph.add_edge("safety_check", END)
app = graph.compile()
