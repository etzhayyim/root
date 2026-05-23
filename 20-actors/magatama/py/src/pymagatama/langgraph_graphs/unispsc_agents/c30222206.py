from typing import TypedDict
from langgraph.graph import StateGraph, END

class BaseStationState(TypedDict):
    equipment_id: str
    frequency_band: str
    compliance_checked: bool
    export_license_validated: bool

def validate_specs(state: BaseStationState):
    print(f"Validating specs for {state['equipment_id']}...")
    return {"compliance_checked": True}

def check_export_controls(state: BaseStationState):
    print("Checking dual-use regulations...")
    return {"export_license_validated": True}

graph = StateGraph(BaseStationState)
graph.add_node("validate", validate_specs)
graph.add_node("export_check", check_export_controls)
graph.set_entry_point("validate")
graph.add_edge("validate", "export_check")
graph.add_edge("export_check", END)
graph = graph.compile()
