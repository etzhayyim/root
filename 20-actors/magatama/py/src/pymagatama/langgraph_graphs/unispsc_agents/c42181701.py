from typing import TypedDict
from langgraph.graph import StateGraph, END

class EKGState(TypedDict):
    device_id: str
    compliance_checked: bool
    calibration_status: str

def validate_specs(state: EKGState):
    print(f"Validating ECG specs for {state['device_id']}")
    return {"compliance_checked": True}

def perform_calibration(state: EKGState):
    print("Running electrical calibration workflow...")
    return {"calibration_status": "PASSED"}

graph = StateGraph(EKGState)
graph.add_node("validate", validate_specs)
graph.add_node("calibrate", perform_calibration)
graph.set_entry_point("validate")
graph.add_edge("validate", "calibrate")
graph.add_edge("calibrate", END)
graph = graph.compile()