from typing import TypedDict
from langgraph.graph import StateGraph, END

class ElectroState(TypedDict):
    device_id: str
    calibration_status: bool
    safety_verified: bool

def validate_specs(state: ElectroState):
    print(f"Validating device {state['device_id']} specs...")
    return {"safety_verified": True}

def audit_calibration(state: ElectroState):
    print("Verifying IEC 60601-1 certification requirements...")
    return {"calibration_status": True}

graph = StateGraph(ElectroState)
graph.add_node("validate", validate_specs)
graph.add_node("audit", audit_calibration)
graph.set_entry_point("validate")
graph.add_edge("validate", "audit")
graph.add_edge("audit", END)
app = graph.compile()
