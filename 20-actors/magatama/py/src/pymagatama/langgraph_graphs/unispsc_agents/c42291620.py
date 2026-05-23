from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_id: str
    is_sterile: bool
    compliance_docs: List[str]
    validation_status: str

def validate_compliance(state: ProcurementState):
    checks = ["ISO_13485", "CE_Mark"] if state['is_sterile'] else []
    return {"validation_status": "COMPLIANT" if all(c in state['compliance_docs'] for c in checks) else "FAILED"}

def route_by_status(state: ProcurementState):
    return "compliant" if state['validation_status'] == "COMPLIANT" else END

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_compliance)
graph.add_edge("validate", END)
graph.set_entry_point("validate")
graph = graph.compile()
