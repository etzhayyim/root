from typing import TypedDict
from langgraph.graph import StateGraph, END

class TissueClosureState(TypedDict):
    product_id: str
    is_sterile: bool
    compliance_docs: list
    approval_status: str

def validate_sterilization(state: TissueClosureState):
    return {"is_sterile": True}

def check_compliance(state: TissueClosureState):
    return {"approval_status": "APPROVED" if len(state['compliance_docs']) > 0 else "PENDING"}

builder = StateGraph(TissueClosureState)
builder.add_node("validate", validate_sterilization)
builder.add_node("compliance", check_compliance)
builder.add_edge("validate", "compliance")
builder.add_edge("compliance", END)
builder.set_entry_point("validate")
graph = builder.compile()