from typing import TypedDict
from langgraph.graph import StateGraph, END

class ThermalState(TypedDict):
    device_id: str
    resolution: int
    calibration_status: bool
    export_compliant: bool

def validate_specs(state: ThermalState):
    if state['resolution'] < 160:
        return {'export_compliant': False}
    return {'export_compliant': True}

def process_export_check(state: ThermalState):
    if not state.get('export_compliant'):
        print("Flagging for dual-use review.")
    return state

graph = StateGraph(ThermalState)
graph.add_node("validate", validate_specs)
graph.add_node("export_review", process_export_check)
graph.set_entry_point("validate")
graph.add_edge("validate", "export_review")
graph.add_edge("export_review", END)
graph = graph.compile()