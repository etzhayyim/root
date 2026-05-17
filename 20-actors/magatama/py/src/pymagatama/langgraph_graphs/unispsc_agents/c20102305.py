from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END

class MiningComponentState(TypedDict):
    component_id: str
    material_data: Dict[str, Any]
    validation_results: List[str]
    approved: bool

def validate_material_specs(state: MiningComponentState) -> MiningComponentState:
    material = state.get("material_data", {})
    hardness = material.get("hardness", 0)
    if hardness > 50:
        state["validation_results"].append("Hardness within acceptable range.")
    else:
        state["validation_results"].append("Hardness check failed.")
    return state

def check_compliance(state: MiningComponentState) -> MiningComponentState:
    state["approved"] = "Hardness check failed." not in state["validation_results"]
    return state

graph = StateGraph(MiningComponentState)
graph.add_node("validate", validate_material_specs)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
app = graph.compile()