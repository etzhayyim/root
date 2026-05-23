from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class WildlifeProcurementState(TypedDict):
    spec_data: dict
    validation_logs: Annotated[list[str], operator.add]
    status: str

def validate_health_certs(state: WildlifeProcurementState):
    spec = state['spec_data']
    logs = [f'Validating certification for {spec.get("species")}']
    if "health_cert" in spec:
        return {"validation_logs": logs, "status": "certs_validated"}
    return {"validation_logs": logs + ["Missing health certificate"], "status": "failed"}

def process_transport_logistics(state: WildlifeProcurementState):
    return {"validation_logs": ["Logistics routing optimized for live animal welfare"], "status": "ready_for_dispatch"}

graph = StateGraph(WildlifeProcurementState)
graph.add_node("validate", validate_health_certs)
graph.add_node("logistics", process_transport_logistics)
graph.add_edge("validate", "logistics")
graph.add_edge("logistics", END)
graph.set_entry_point("validate")
app = graph.compile()
