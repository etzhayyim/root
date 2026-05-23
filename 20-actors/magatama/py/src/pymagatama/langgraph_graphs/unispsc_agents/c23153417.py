from typing import TypedDict
from langgraph.graph import StateGraph, END

class LaserWeldState(TypedDict):
    equipment_id: str
    safety_check: bool
    calibrated: bool
    approved: bool

def validate_safety(state: LaserWeldState):
    print(f'Validating safety for {state["equipment_id"]}')
    return {"safety_check": True}

def verify_calibration(state: LaserWeldState):
    print(f'Verifying calibration for {state["equipment_id"]}')
    return {"calibrated": True}

graph = StateGraph(LaserWeldState)
graph.add_node("validate_safety", validate_safety)
graph.add_node("verify_calibration", verify_calibration)
graph.set_entry_point("validate_safety")
graph.add_edge("validate_safety", "verify_calibration")
graph.add_edge("verify_calibration", END)
graph = graph.compile()
