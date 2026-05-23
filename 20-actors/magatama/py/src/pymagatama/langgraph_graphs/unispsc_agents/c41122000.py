from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabSyringeState(TypedDict):
    syringe_type: str
    volume: float
    has_calibration_cert: bool
    is_approved: bool

def validate_syringe_spec(state: LabSyringeState):
    if state['has_calibration_cert'] and state['volume'] > 0:
        return {"is_approved": True}
    return {"is_approved": False}

graph = StateGraph(LabSyringeState)
graph.add_node("validate", validate_syringe_spec)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()
