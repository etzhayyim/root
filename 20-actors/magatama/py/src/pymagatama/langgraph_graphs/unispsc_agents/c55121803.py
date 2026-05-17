from typing import TypedDict
from langgraph.graph import StateGraph, END
class PassportState(TypedDict):
    document_id: str
    security_verified: bool
    transit_status: str
def verify_security(state: PassportState) -> PassportState:
    print(f'Verifying security protocols for {state["document_id"]}')
    return {**state, "security_verified": True}
def log_chain_of_custody(state: PassportState) -> PassportState:
    print('Logging chain of custody for secure shipment.')
    return {**state, "transit_status": "SECURE_TRANSIT"}
graph = StateGraph(PassportState)
graph.add_node("verify", verify_security)
graph.add_node("log_shipment", log_chain_of_custody)
graph.set_entry_point("verify")
graph.add_edge("verify", "log_shipment")
graph.add_edge("log_shipment", END)
graph = graph.compile()