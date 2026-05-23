from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DentalProductState(TypedDict):
    product_id: str
    compliance_docs: List[str]
    status: str

def validate_compliance(state: DentalProductState):
    if "ISO_13485" in state["compliance_docs"]:
        return {"status": "validated"}
    return {"status": "flagged_for_review"}

def process_accessory(state: DentalProductState):
    print(f"Processing dental accessory: {state['product_id']}")
    return {"status": "ready_for_procurement"}

builder = StateGraph(DentalProductState)
builder.add_node("validate", validate_compliance)
builder.add_node("process", process_accessory)
builder.set_entry_point("validate")
builder.add_edge("validate", "process")
builder.add_edge("process", END)
graph = builder.compile()
