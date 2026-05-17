from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    temp_log: list[float]
    is_gmp: bool
    valid: bool

def validate_pharmaceutical(state: ProcurementState) -> dict:
    is_valid = state['purity'] >= 99.0 and state['is_gmp'] and all(t <= 8.0 for t in state['temp_log'])
    print(f"Validation result: {is_valid}")
    return {"valid": is_valid}

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_pharmaceutical)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
compile_graph = graph.compile()