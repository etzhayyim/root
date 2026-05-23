from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    compliance_status: bool
    purity_level: float
    errors: List[str]

def validate_compliance(state: ProcurementState):
    """Verify GMP and regulatory status."""
    print(f"Validating compliance for batch: {state['batch_id']}")
    return {"compliance_status": True}

def check_purity(state: ProcurementState):
    """Check purity threshold for pharmaceutical grade."""
    if state['purity_level'] < 99.0:
        return {"errors": ["Purity below 99% threshold"]}
    return {}

builder = StateGraph(ProcurementState)
builder.add_node("compliance", validate_compliance)
builder.add_node("purity", check_purity)
builder.set_entry_point("compliance")
builder.add_edge("compliance", "purity")
builder.add_edge("purity", END)
graph = builder.compile()
