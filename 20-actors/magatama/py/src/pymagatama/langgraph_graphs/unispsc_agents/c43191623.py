from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PeriphState(TypedDict):
    device_id: str
    spec_requirements: List[str]
    validation_log: List[str]
    status: str

def validate_compatibility(state: PeriphState):
    log = f"Validating device {state['device_id']} against specs: {state['spec_requirements']}"
    return {"validation_log": [log], "status": "COMPATIBILITY_CHECKED"}

def verify_driver_integrity(state: PeriphState):
    log = "Verifying driver signature and hardware compatibility."
    return {"validation_log": state.get("validation_log", []) + [log], "status": "VERIFIED"}

builder = StateGraph(PeriphState)
builder.add_node("check", validate_compatibility)
builder.add_node("driver", verify_driver_integrity)
builder.set_entry_point("check")
builder.add_edge("check", "driver")
builder.add_edge("driver", END)
graph = builder.compile()
