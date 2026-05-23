from typing import TypedDict
from langgraph.graph import StateGraph, END

class RaspberryFlowState(TypedDict):
    quality_score: float
    temp_check: bool
    approved: bool

def validate_freshness(state: RaspberryFlowState):
    return { "temp_check": state["quality_score"] > 0.8 }

def finalize_intake(state: RaspberryFlowState):
    return { "approved": state["temp_check"] }

graph = StateGraph(RaspberryFlowState)
graph.add_node("validate", validate_freshness)
graph.add_node("finalize", finalize_intake)
graph.set_entry_point("validate")
graph.add_edge("validate", "finalize")
graph.add_edge("finalize", END)
app = graph.compile()
