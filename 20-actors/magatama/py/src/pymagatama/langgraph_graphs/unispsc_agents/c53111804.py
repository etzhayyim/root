from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ShoeProcurementState(TypedDict):
    material_specs: dict
    compliance_docs: List[str]
    approved: bool

def validate_material(state: ShoeProcurementState):
    # Business logic for checking material non-toxicity
    state['approved'] = all(m in ["Leather", "Synthetic", "Rubber"] for m in state['material_specs'])
    return state

def check_compliance(state: ShoeProcurementState):
    # Verification of safety certificates
    if len(state['compliance_docs']) < 2: state['approved'] = False
    return state

builder = StateGraph(ShoeProcurementState)
builder.add_node("validate_material", validate_material)
builder.add_node("check_compliance", check_compliance)
builder.set_entry_point("validate_material")
builder.add_edge("validate_material", "check_compliance")
builder.add_edge("check_compliance", END)
graph = builder.compile()
