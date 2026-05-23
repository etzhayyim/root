from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class ExplosiveState(TypedDict):
    quantity: float
    destination: str
    compliance_passed: bool
    safety_check_logs: Annotated[list, operator.add]

def validate_transport_compliance(state: ExplosiveState):
    # Simulated compliance validation logic
    is_compliant = state['quantity'] < 1000 and "secured_zone" in state['destination']
    return {"compliance_passed": is_compliant, "safety_check_logs": [f"Compliance status: {is_compliant}"]}

def route_by_compliance(state: ExplosiveState):
    return "ready" if state["compliance_passed"] else END

def stage_delivery(state: ExplosiveState):
    return {"safety_check_logs": ["Delivery successfully staged and secured for transport"]}

graph = StateGraph(ExplosiveState)
graph.add_node("validate", validate_transport_compliance)
graph.add_node("ready", stage_delivery)
graph.add_edge("validate", "ready")
graph.add_conditional_edges("validate", route_by_compliance, {"ready": "ready", END: END})
graph.set_entry_point("validate")
graph.add_edge("ready", END)
graph = graph.compile()
