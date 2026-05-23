from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class ResinState(TypedDict):
    purity: float
    viscosity: float
    status: str

def validate_purity(state: ResinState):
    new_status = "validated" if state["purity"] >= 99.9 else "rejected"
    return {"status": new_status}

def process_curing_cycle(state: ResinState):
    return {"status": "curing_complete"}

graph = StateGraph(ResinState)
graph.add_node("validate", validate_purity)
graph.add_node("process", process_curing_cycle)
graph.set_entry_point("validate")
graph.add_edge("validate", "process")
graph.add_edge("process", END)
compiled_graph = graph.compile()
