from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MetalState(TypedDict):
    material_id: str
    purity_level: float
    spec_verified: bool
    compliance_risk: List[str]

def validate_material(state: MetalState):
    # Simulate spectroscopic validation logic
    verified = state['purity_level'] >= 99.9
    return {"spec_verified": verified}

def check_compliance(state: MetalState):
    risks = []
    if state['purity_level'] > 99.99:
        risks.append("dual-use-export-control")
    return {"compliance_risk": risks}

builder = StateGraph(MetalState)
builder.add_node("validate", validate_material)
builder.add_node("compliance", check_compliance)
builder.add_edge("validate", "compliance")
builder.add_edge("compliance", END)
builder.set_entry_point("validate")
graph = builder.compile()