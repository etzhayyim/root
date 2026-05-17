from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugState(TypedDict):
    purity: float
    safety_checked: bool
    compliant: bool

def validate_purity(state: DrugState):
    return {"compliant": state['purity'] >= 0.99}

def check_safety(state: DrugState):
    return {"safety_checked": True}

graph = StateGraph(DrugState)
graph.add_node("validate", validate_purity)
graph.add_node("safety", check_safety)
graph.add_edge("validate", "safety")
graph.add_edge("safety", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()