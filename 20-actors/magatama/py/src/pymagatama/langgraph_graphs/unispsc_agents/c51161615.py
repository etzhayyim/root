from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    compliance_docs: bool
    purity_level: float

def validate_purity(state: ProcurementState):
    return {"compliance_docs": state["purity_level"] >= 0.99}

def update_status(state: ProcurementState):
    print(f"Processing batch {state['batch_id']}: Compliance status {state['compliance_docs']}")
    return state

workflow = StateGraph(ProcurementState)
workflow.add_node("validate", validate_purity)
workflow.add_node("log", update_status)
workflow.set_entry_point("validate")
workflow.add_edge("validate", "log")
workflow.add_edge("log", END)

graph = workflow.compile()
