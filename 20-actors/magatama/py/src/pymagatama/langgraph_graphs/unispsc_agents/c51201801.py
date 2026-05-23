from typing import TypedDict
from langgraph.graph import StateGraph, END

class ImmunoglobulinState(TypedDict):
    purity: float
    temp_log: list
    is_validated: bool

def check_purity(state: ImmunoglobulinState):
    return {"is_validated": state["purity"] >= 0.99}

def verify_storage(state: ImmunoglobulinState):
    return {"is_validated": all(t <= -20 for t in state["temp_log"])}

graph = StateGraph(ImmunoglobulinState)
graph.add_node("check_purity", check_purity)
graph.add_node("verify_storage", verify_storage)
graph.set_entry_point("check_purity")
graph.add_edge("check_purity", "verify_storage")
graph.add_edge("verify_storage", END)
graph = graph.compile()
