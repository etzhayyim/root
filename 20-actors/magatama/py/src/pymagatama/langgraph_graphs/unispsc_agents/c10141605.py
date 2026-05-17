from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class FeedState(TypedDict):
    batch_id: str
    purity_check: bool
    safety_verified: bool
    log: Annotated[Sequence[str], operator.add]

def validate_batch(state: FeedState) -> FeedState:
    # Simulate purity validation logic
    is_pure = True 
    return {"purity_check": is_pure, "log": [f"Batch {state['batch_id']} purity verified: {is_pure}"]}

def verify_safety(state: FeedState) -> FeedState:
    # Simulate safety compliance check
    is_safe = state.get("purity_check", False)
    return {"safety_verified": is_safe, "log": [f"Safety verification status: {is_safe}"]}

builder = StateGraph(FeedState)
builder.add_node("validate", validate_batch)
builder.add_node("safety", verify_safety)
builder.set_entry_point("validate")
builder.add_edge("validate", "safety")
builder.add_edge("safety", END)
graph = builder.compile()