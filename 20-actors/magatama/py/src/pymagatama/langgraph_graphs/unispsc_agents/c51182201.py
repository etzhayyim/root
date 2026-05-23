from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    batch_id: str
    compliance_cleared: bool
    check_temp_log: bool

def validate_cold_chain(state: ProcurementState):
    # Simulate cold chain validation logic
    state['check_temp_log'] = True
    print(f"Validating cold chain for {state['item_name']}")
    return state

def verify_regulatory(state: ProcurementState):
    # Simulate GMP/FDA regulatory check
    state['compliance_cleared'] = True
    return state

graph = StateGraph(ProcurementState)
graph.add_node("validate_cold_chain", validate_cold_chain)
graph.add_node("verify_regulatory", verify_regulatory)
graph.set_entry_point("validate_cold_chain")
graph.add_edge("validate_cold_chain", "verify_regulatory")
graph.add_edge("verify_regulatory", END)
graph = graph.compile()
