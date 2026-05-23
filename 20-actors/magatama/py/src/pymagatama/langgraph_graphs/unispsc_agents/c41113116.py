from typing import TypedDict
from langgraph.graph import StateGraph, END

class GasDetectionState(TypedDict):
    gas_type: str
    concentration: float
    expiry_check: bool
    is_compliant: bool

def validate_expiry(state: GasDetectionState):
    return {"expiry_check": True}

def check_compliance(state: GasDetectionState):
    compliant = state["expiry_check"] and state["concentration"] > 0
    return {"is_compliant": compliant}

builder = StateGraph(GasDetectionState)
builder.add_node("validate_expiry", validate_expiry)
builder.add_node("check_compliance", check_compliance)
builder.set_entry_point("validate_expiry")
builder.add_edge("validate_expiry", "check_compliance")
builder.add_edge("check_compliance", END)
graph = builder.compile()
