from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DrugProcurementState(TypedDict):
    product_id: str
    quality_docs: List[str]
    approved: bool

def validate_gmp_cert(state: DrugProcurementState):
    return {"approved": "GMP_CERT" in state["quality_docs"]}

def audit_log(state: DrugProcurementState):
    print(f"Processing drug: {state['product_id']} Status: {state['approved']}")
    return {}

graph = StateGraph(DrugProcurementState)
graph.add_node("validate", validate_gmp_cert)
graph.add_node("audit", audit_log)
graph.set_entry_point("validate")
graph.add_edge("validate", "audit")
graph.add_edge("audit", END)
graph = graph.compile()
