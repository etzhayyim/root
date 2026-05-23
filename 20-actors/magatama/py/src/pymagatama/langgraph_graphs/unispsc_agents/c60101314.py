from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FlashCardState(TypedDict):
    card_content: str
    quality_check: bool
    approved: bool

def validate_readability(state: FlashCardState):
    return {"quality_check": len(state['card_content']) > 0}

def final_approval(state: FlashCardState):
    return {"approved": state['quality_check']}

graph = StateGraph(FlashCardState)
graph.add_node("validate", validate_readability)
graph.add_node("approve", final_approval)
graph.add_edge("validate", "approve")
graph.add_edge("approve", END)
graph.set_entry_point("validate")
graph = graph.compile()
