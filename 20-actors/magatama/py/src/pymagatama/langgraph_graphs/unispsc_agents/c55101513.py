from typing import TypedDict
from langgraph.graph import StateGraph, END

class TradeCardState(TypedDict):
    card_id: str
    condition_grade: float
    verified: bool

def validate_card(state: TradeCardState):
    print(f"Validating card: {state['card_id']}")
    return {"verified": state['condition_grade'] > 7.0}

def finalize_procurement(state: TradeCardState):
    print(f"Card verification result: {state['verified']}")
    return {"verified": state['verified']}

graph = StateGraph(TradeCardState)
graph.add_node("validate", validate_card)
graph.add_node("finalize", finalize_procurement)
graph.set_entry_point("validate")
graph.add_edge("validate", "finalize")
graph.add_edge("finalize", END)
graph = graph.compile()
