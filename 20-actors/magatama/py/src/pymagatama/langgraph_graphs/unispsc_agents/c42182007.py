from typing import TypedDict
from langgraph.graph import StateGraph, END

class LampProcurementState(TypedDict):
    lamp_type: str
    quality_cert: bool
    is_approved_vendor: bool

def validate_lamp_specs(state: LampProcurementState):
    return {"quality_cert": state['lamp_type'] == "medical_grade"}

def check_vendor_status(state: LampProcurementState):
    return {"is_approved_vendor": True}

graph = StateGraph(LampProcurementState)
graph.add_node("validate", validate_lamp_specs)
graph.add_node("vendor_check", check_vendor_status)
graph.set_entry_point("validate")
graph.add_edge("validate", "vendor_check")
graph.add_edge("vendor_check", END)
graph = graph.compile()