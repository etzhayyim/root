from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_number: str
    gmp_compliance: bool
    expiry_check: bool

def validate_gmp(state: ProcurementState):
    print(f'Validating batch {state["batch_number"]} for GMP compliance.')
    return {'gmp_compliance': True}

def verify_shelf_life(state: ProcurementState):
    print('Checking expiration date against procurement policy.')
    return {'expiry_check': True}

graph = StateGraph(ProcurementState)
graph.add_node("validate_gmp", validate_gmp)
graph.add_node("verify_shelf_life", verify_shelf_life)
graph.set_entry_point("validate_gmp")
graph.add_edge("validate_gmp", "verify_shelf_life")
graph.add_edge("verify_shelf_life", END)
graph = graph.compile()
