from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugState(TypedDict):
    batch_id: str
    compliance_passed: bool
    temp_log_verified: bool

def validate_gmp(state: DrugState):
    print(f"Validating GMP for {state['batch_id']}")
    return {"compliance_passed": True}

def check_temp(state: DrugState):
    print("Verifying cold-chain logs")
    return {"temp_log_verified": True}

graph = StateGraph(DrugState)
graph.add_node("validate_gmp", validate_gmp)
graph.add_node("check_temp", check_temp)
graph.set_entry_point("validate_gmp")
graph.add_edge("validate_gmp", "check_temp")
graph.add_edge("check_temp", END)
graph = graph.compile()
