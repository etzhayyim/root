from typing import TypedDict
from langgraph.graph import StateGraph, END

class AbrasiveState(TypedDict):
    material_type: str
    grit_size: int
    safety_compliant: bool

def validate_abrasive(state: AbrasiveState):
    return {"safety_compliant": state.get("material_type") != "" and state.get("grit_size") > 0}

graph = StateGraph(AbrasiveState)
graph.add_node("validate", validate_abrasive)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
compiled_graph = graph.compile()
