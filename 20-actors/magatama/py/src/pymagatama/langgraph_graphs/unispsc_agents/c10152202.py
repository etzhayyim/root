from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class ProcurementState(TypedDict):
    commodity_id: str
    spec_data: dict
    validation_results: Annotated[list, operator.add]
    is_compliant: bool

def validate_specs(state: ProcurementState):
    specs = state.get("spec_data", {})
    # Logic to validate specialized oil/drilling equipment standards
    results = []
    if "explosion_proof_rating" not in specs:
        results.append("Missing explosion proof rating")
    return {"validation_results": results, "is_compliant": len(results) == 0}

def route_by_compliance(state: ProcurementState):
    return "compliant_path" if state["is_compliant"] else "review_path"

def log_compliant(state: ProcurementState):
    print(f"Commodity {state['commodity_id']} validated successfully.")
    return {}

def escalate_review(state: ProcurementState):
    print(f"Flagging {state['commodity_id']} for hazardous/sanctions review.")
    return {}

builder = StateGraph(ProcurementState)
builder.add_node("validate", validate_specs)
builder.add_node("compliant_path", log_compliant)
builder.add_node("review_path", escalate_review)
builder.set_entry_point("validate")
builder.add_conditional_edges("validate", route_by_compliance)
builder.add_edge("compliant_path", END)
builder.add_edge("review_path", END)
graph = builder.compile()
