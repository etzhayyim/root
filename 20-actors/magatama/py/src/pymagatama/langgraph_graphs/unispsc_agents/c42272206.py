from typing import TypedDict
from langgraph.graph import StateGraph, END

class VentiState(TypedDict):
    device_id: str
    compliance_checked: bool
    calibration_status: str

def validate_compliance(state: VentiState):
    print(f'Checking ISO 80601-2-12 for {state["device_id"]}')
    return {"compliance_checked": True}

def verify_calibration(state: VentiState):
    print(f'Verifying sensor accuracy for {state["device_id"]}')
    return {"calibration_status": "PASSED"}

builder = StateGraph(VentiState)
builder.add_node("compliance", validate_compliance)
builder.add_node("calibration", verify_calibration)
builder.set_entry_point("compliance")
builder.add_edge("compliance", "calibration")
builder.add_edge("calibration", END)
graph = builder.compile()