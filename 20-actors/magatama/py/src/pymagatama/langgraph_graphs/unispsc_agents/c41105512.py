from typing import TypedDict
from langgraph.graph import StateGraph, END

class PurificationState(TypedDict):
    sample_type: str
    purity_check: bool
    qc_passed: bool

def validate_sample(state: PurificationState):
    print(f"Validating extraction for: {state['sample_type']}")
    return {"purity_check": True}

def perform_qc(state: PurificationState):
    return {"qc_passed": state['purity_check'] and True}

graph = StateGraph(PurificationState)
graph.add_node("validate", validate_sample)
graph.add_node("qc", perform_qc)
graph.set_entry_point("validate")
graph.add_edge("validate", "qc")
graph.add_edge("qc", END)
compile_graph = graph.compile()