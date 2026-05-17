from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MortuaryState(TypedDict):
    compound_name: str
    sds_verified: bool
    toxicity_level: float
    approval_status: bool

def validate_safety_data(state: MortuaryState):
    # Business logic for OSHA/GHS compliance check
    state["sds_verified"] = True
    return state

def check_toxicity(state: MortuaryState):
    # Logic to ensure compound falls within safe regulatory limits
    state["approval_status"] = state["toxicity_level"] < 0.05
    return state

graph = StateGraph(MortuaryState)
graph.add_node("validate", validate_safety_data)
graph.add_node("toxicity", check_toxicity)
graph.add_edge("validate", "toxicity")
graph.add_edge("toxicity", END)
graph.set_entry_point("validate")
graph = graph.compile()