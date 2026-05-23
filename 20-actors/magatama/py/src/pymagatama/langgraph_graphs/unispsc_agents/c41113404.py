from typing import TypedDict
from langgraph.graph import StateGraph, END

class RadiationCounterState(TypedDict):
    device_id: str
    calibration_status: bool
    sensitivity_check: float
    status: str

def validate_calibration(state: RadiationCounterState):
    return {"calibration_status": state["sensitivity_check"] > 0.95}

def perform_safety_check(state: RadiationCounterState):
    return {"status": "READY" if state["calibration_status"] else "REJECTED"}

graph = StateGraph(RadiationCounterState)
graph.add_node("calibrate", validate_calibration)
graph.add_node("safety", perform_safety_check)
graph.add_edge("calibrate", "safety")
graph.add_edge("safety", END)
graph.set_entry_point("calibrate")
compiled_graph = graph.compile()
