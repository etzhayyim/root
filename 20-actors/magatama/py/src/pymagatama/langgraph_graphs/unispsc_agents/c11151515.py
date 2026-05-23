from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MetalPowderState(TypedDict):
    purity: float
    particle_size: float
    safety_clearance: bool
    validation_log: List[str]

def validate_purity(state: MetalPowderState):
    log = state.get("validation_log", [])
    if state["purity"] >= 99.9:
        log.append("Purity standard met.")
    else:
        log.append("Purity below threshold.")
    return {"validation_log": log}

def check_safety(state: MetalPowderState):
    log = state.get("validation_log", [])
    if state.get("safety_clearance", False):
        log.append("Safety clearance verified.")
    else:
        log.append("Safety clearance failed.")
    return {"validation_log": log}

graph = StateGraph(MetalPowderState)
graph.add_node("validate_purity", validate_purity)
graph.add_node("check_safety", check_safety)
graph.add_edge("validate_purity", "check_safety")
graph.add_edge("check_safety", END)
graph.set_entry_point("validate_purity")
graph = graph.compile()
