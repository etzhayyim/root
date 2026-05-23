from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalDeviceState(TypedDict):
    device_id: str
    compliance_doc: str
    is_approved: bool

def validate_certification(state: SurgicalDeviceState):
    state["is_approved"] = "ISO-13485" in state["compliance_doc"]
    return state

def check_sterility(state: SurgicalDeviceState):
    if not state["is_approved"]:
        return "reject"
    return "approve"

graph = StateGraph(SurgicalDeviceState)
graph.add_node("validate", validate_certification)
graph.add_conditional_edges("validate", check_sterility, {"approve": END, "reject": END})
graph.set_entry_point("validate")
graph = graph.compile()
