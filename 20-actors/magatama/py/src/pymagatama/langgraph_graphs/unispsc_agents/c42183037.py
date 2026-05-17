from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProjectorState(TypedDict):
    model_id: str
    compliance_verified: bool
    calibration_status: str

def validate_specs(state: ProjectorState):
    print(f"Validating medical compliance for {state['model_id']}")
    return {"compliance_verified": True}

def check_calibration(state: ProjectorState):
    return {"calibration_status": "Passed"}

graph = StateGraph(ProjectorState)
graph.add_node("validate", validate_specs)
graph.add_node("calibrate", check_calibration)
graph.set_entry_point("validate")
graph.add_edge("validate", "calibrate")
graph.add_edge("calibrate", END)
graph = graph.compile()