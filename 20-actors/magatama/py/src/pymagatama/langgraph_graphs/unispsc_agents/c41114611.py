from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class HardnessTestState(TypedDict):
    equipment_id: str
    calibration_date: str
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: HardnessTestState):
    if state.get("calibration_date"):
        state["is_compliant"] = True
        state["validation_log"].append("Calibration date verified.")
    return state

def finalize_procurement(state: HardnessTestState):
    state["validation_log"].append("Procurement workflow finalized.")
    return state

graph = StateGraph(HardnessTestState)
graph.add_node("validate", validate_specs)
graph.add_node("finalize", finalize_procurement)
graph.set_entry_point("validate")
graph.add_edge("validate", "finalize")
graph.add_edge("finalize", END)
graph = graph.compile()