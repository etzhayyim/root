from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class TargetState(TypedDict):
    purity: float
    surface_check: bool
    validation_log: List[str]

def purity_check(state: TargetState):
    log = state.get("validation_log", [])
    if state["purity"] >= 99.999:
        log.append("Purity 5N confirmed.")
    else:
        log.append("Purity insufficient for semiconductor grade.")
    return {"validation_log": log}

def surface_inspection(state: TargetState):
    log = state.get("validation_log", [])
    if state.get("surface_check", False):
        log.append("Surface integrity verified.")
    else:
        log.append("Surface failed inspection.")
    return {"validation_log": log}

graph = StateGraph(TargetState)
graph.add_node("purity_check", purity_check)
graph.add_node("surface_inspection", surface_inspection)
graph.add_edge("purity_check", "surface_inspection")
graph.add_edge("surface_inspection", END)
graph.set_entry_point("purity_check")
graph = graph.compile()
