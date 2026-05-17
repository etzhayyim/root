from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OrthopedicState(TypedDict):
    product_id: str
    compliance_docs: List[str]
    is_approved: bool

def validate_compliance(state: OrthopedicState):
    # Simulate validation of medical requirements
    return {"is_approved": len(state["compliance_docs"]) >= 3}

def update_status(state: OrthopedicState):
    print(f"Processing orthopedic product {state['product_id']}")
    return {"is_approved": True}

graph = StateGraph(OrthopedicState)
graph.add_node("validate", validate_compliance)
graph.add_node("finalize", update_status)
graph.set_entry_point("validate")
graph.add_edge("validate", "finalize")
graph.add_edge("finalize", END)
graph = graph.compile()