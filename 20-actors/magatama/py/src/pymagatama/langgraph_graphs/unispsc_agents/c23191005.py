from typing import TypedDict
from langgraph.graph import StateGraph, END

class LaserProcurementState(TypedDict):
    specs: dict
    safety_verified: bool
    export_cleared: bool

def validate_specs(state: LaserProcurementState):
    """Validates laser power vs safety constraints."""
    print(f"Validating specs: {state['specs']}")
    return {'safety_verified': state['specs'].get('power', 0) < 50}

def check_compliance(state: LaserProcurementState):
    """Checks dual-use export control status."""
    return {'export_cleared': True}

builder = StateGraph(LaserProcurementState)
builder.add_node("validate", validate_specs)
builder.add_node("compliance", check_compliance)
builder.set_entry_point("validate")
builder.add_edge("validate", "compliance")
builder.add_edge("compliance", END)
graph = builder.compile()
