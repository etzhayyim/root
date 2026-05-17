from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugProcurementState(TypedDict):
    batch_id: str
    compliance_checked: bool
    gmp_status: str

def validate_gmp(state: DrugProcurementState):
    print(f'Validating GMP status for batch: {state["batch_id"]}')
    return {"compliance_checked": state["gmp_status"] == "Certified"}

def route_by_compliance(state: DrugProcurementState):
    return "ready" if state["compliance_checked"] else "reject"

graph = StateGraph(DrugProcurementState)
graph.add_node("validate", validate_gmp)
graph.set_entry_point("validate")
graph.add_conditional_edges("validate", route_by_compliance, {"ready": END, "reject": END})
graph.compile()