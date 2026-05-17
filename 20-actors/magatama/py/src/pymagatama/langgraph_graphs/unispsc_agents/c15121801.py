from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class ConduitState(TypedDict):
    material_spec: str
    pressure_rating: float
    inspection_status: List[str]
    is_compliant: bool

def validate_material(state: ConduitState) -> ConduitState:
    if "steel" in state["material_spec"].lower():
        state["inspection_status"].append("Material validated: Metal")
    return state

def check_pressure(state: ConduitState) -> ConduitState:
    if state["pressure_rating"] > 1.0:
        state["inspection_status"].append("Pressure rating passed")
        state["is_compliant"] = True
    else:
        state["is_compliant"] = False
    return state

workflow = StateGraph(ConduitState)
workflow.add_node("validate", validate_material)
workflow.add_node("pressure", check_pressure)
workflow.set_entry_point("validate")
workflow.add_edge("validate", "pressure")
workflow.add_edge("pressure", END)

graph = workflow.compile()