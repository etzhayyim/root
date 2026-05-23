from typing import TypedDict
from langgraph.graph import StateGraph, END

class AuditState(TypedDict):
    device_id: str
    certification_verified: bool
    sterilization_validated: bool

def check_cert(state: AuditState):
    print(f"Verifying medical certification for: {state['device_id']}")
    return {'certification_verified': True}

def validate_sterilization(state: AuditState):
    print("Validating autoclave compatibility protocols.")
    return {'sterilization_validated': True}

graph = StateGraph(AuditState)
graph.add_node("check_cert", check_cert)
graph.add_node("validate_sterilization", validate_sterilization)
graph.set_entry_point("check_cert")
graph.add_edge("check_cert", "validate_sterilization")
graph.add_edge("validate_sterilization", END)
compiled_graph = graph.compile()
