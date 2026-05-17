from typing import TypedDict
from langgraph.graph import StateGraph, END

class PerfusionState(TypedDict):
    device_id: str
    compliance_check: bool
    calibration_status: bool

def validate_medical_device(state: PerfusionState):
    print(f'Validating medical device: {state["device_id"]}')
    return {"compliance_check": True}

def verify_calibration(state: PerfusionState):
    print('Verifying perfusion system calibration data...')
    return {"calibration_status": True}

graph = StateGraph(PerfusionState)
graph.add_node("validate", validate_medical_device)
graph.add_node("calibrate", verify_calibration)
graph.set_entry_point("validate")
graph.add_edge("validate", "calibrate")
graph.add_edge("calibrate", END)
app = graph.compile()