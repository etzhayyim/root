from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SiliconState(TypedDict):
    purity: float
    resistivity: float
    status: str
    validation_log: List[str]

def validate_material(state: SiliconState) -> SiliconState:
    logs = state.get("validation_log", [])
    if state["purity"] < 99.9999999:
        state["status"] = "REJECTED"
        logs.append("Purity below electronic grade standards")
    else:
        state["status"] = "VALIDATED"
        logs.append("Purity check passed")
    return {"status": state["status"], "validation_log": logs}

def check_resistivity(state: SiliconState) -> SiliconState:
    logs = state.get("validation_log", [])
    if 0.01 <= state["resistivity"] <= 1000:
        logs.append("Resistivity within operating range")
    else:
        state["status"] = "REJECTED"
        logs.append("Resistivity out of tolerance")
    return {"status": state["status"], "validation_log": logs}

builder = StateGraph(SiliconState)
builder.add_node("validate", validate_material)
builder.add_node("resistivity", check_resistivity)
builder.add_edge("validate", "resistivity")
builder.add_edge("resistivity", END)
builder.set_entry_point("validate")
graph = builder.compile()