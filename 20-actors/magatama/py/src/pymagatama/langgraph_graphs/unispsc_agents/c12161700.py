from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class CatalystState(TypedDict):
    purity: float
    safety_clearance: bool
    history: Annotated[List[str], add_messages]

def validate_catalyst_purity(state: CatalystState) -> dict:
    return {"safety_clearance": state["purity"] >= 0.99}

def process_safety_check(state: CatalystState) -> dict:
    if not state["safety_clearance"]:
        return {"history": ["Safety check failed: Purity below standard"]}
    return {"history": ["Safety check passed: Ready for industrial deployment"]}

graph = StateGraph(CatalystState)
graph.add_node("validate", validate_catalyst_purity)
graph.add_node("safety", process_safety_check)
graph.set_entry_point("validate")
graph.add_edge("validate", "safety")
graph.add_edge("safety", END)
graph = graph.compile()