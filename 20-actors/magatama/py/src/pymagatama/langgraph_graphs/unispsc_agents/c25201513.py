from typing import TypedDict
from langgraph.graph import StateGraph, END

class RadomeState(TypedDict):
    part_code: str
    rf_specs: dict
    compliance_verified: bool

def validate_specs(state: RadomeState):
    # Simulate RF transmission check
    loss = state['rf_specs'].get('loss', 1.0)
    return {"compliance_verified": loss < 0.5}

def route_verification(state: RadomeState):
    return "verified" if state['compliance_verified'] else "reject"

builder = StateGraph(RadomeState)
builder.add_node("validate", validate_specs)
builder.set_entry_point("validate")
builder.add_edge("validate", END)
graph = builder.compile()