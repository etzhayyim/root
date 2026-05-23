from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AcyclovirState(TypedDict):
    batch_id: str
    purity_check: bool
    gmp_verified: bool
    status: str

def validate_quality(state: AcyclovirState):
    print(f"Validating batch {state['batch_id']} purity...")
    return {'purity_check': True}

def verify_compliance(state: AcyclovirState):
    print("Verifying GMP certification...")
    return {'gmp_verified': True, 'status': 'APPROVED'}

graph = StateGraph(AcyclovirState)
graph.add_node("validate", validate_quality)
graph.add_node("verify", verify_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "verify")
graph.add_edge("verify", END)
graph = graph.compile()
