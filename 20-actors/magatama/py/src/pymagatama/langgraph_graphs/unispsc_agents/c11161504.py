from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CeramicState(TypedDict):
    material_id: str
    purity: float
    particle_distribution: dict
    validation_log: List[str]
    approved: bool

def validate_material(state: CeramicState) -> CeramicState:
    log = state.get("validation_log", [])
    if state["purity"] >= 99.9:
        log.append("High purity validated for semiconductor grade.")
        state["approved"] = True
    else:
        log.append("Purity insufficient for target application.")
        state["approved"] = False
    state["validation_log"] = log
    return state

def perform_inspection(state: CeramicState) -> CeramicState:
    if state["approved"]:
        state["validation_log"].append("Structural inspection passed.")
    return state

graph = StateGraph(CeramicState)
graph.add_node("validate", validate_material)
graph.add_node("inspect", perform_inspection)
graph.set_entry_point("validate")
graph.add_edge("validate", "inspect")
graph.add_edge("inspect", END)
graph = graph.compile()
