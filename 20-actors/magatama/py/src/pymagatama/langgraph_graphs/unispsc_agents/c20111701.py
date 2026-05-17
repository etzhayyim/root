from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PumpProcurementState(TypedDict):
    commodity_code: str
    pressure_spec: float
    flow_rate: float
    is_validated: bool
    validation_log: List[str]

def validate_specs(state: PumpProcurementState) -> PumpProcurementState:
    log = state.get("validation_log", [])
    if state["pressure_spec"] > 70.0:
        log.append("High pressure rating requires extra scrutiny.")
    state["is_validated"] = True
    state["validation_log"] = log
    return state

def check_export_control(state: PumpProcurementState) -> PumpProcurementState:
    if state["pressure_spec"] > 21.0:
        state["validation_log"].append("Potential Dual-Use Export Control flagged.")
    return state

graph = StateGraph(PumpProcurementState)
graph.add_node("validate_specs", validate_specs)
graph.add_node("export_check", check_export_control)
graph.set_entry_point("validate_specs")
graph.add_edge("validate_specs", "export_check")
graph.add_edge("export_check", END)
graph = graph.compile()