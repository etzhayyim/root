from typing import TypedDict
from langgraph.graph import StateGraph, END

class CaffeineState(TypedDict):
    purity: float
    safety_cleared: bool

def validate_purity(state: CaffeineState):
    return {"safety_cleared": state['purity'] >= 99.0}

def route_verification(state: CaffeineState):
    return "process" if state['safety_cleared'] else END

graph = StateGraph(CaffeineState)
graph.add_node("validate", validate_purity)
graph.add_edge("validate", END)
graph.set_entry_point("validate")
graph = graph.compile()
