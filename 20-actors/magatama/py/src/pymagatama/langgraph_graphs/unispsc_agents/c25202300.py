from typing import TypedDict
from langgraph.graph import StateGraph, END

class RestraintState(TypedDict):
    part_number: str
    tso_status: bool
    inspection_passed: bool

def validate_tso(state: RestraintState):
    print(f"Validating TSO for {state['part_number']}")
    return {"tso_status": True}

def perform_safety_check(state: RestraintState):
    print("Running tensile strength inspection")
    return {"inspection_passed": True}

graph = StateGraph(RestraintState)
graph.add_node("validate_tso", validate_tso)
graph.add_node("safety_check", perform_safety_check)
graph.set_entry_point("validate_tso")
graph.add_edge("validate_tso", "safety_check")
graph.add_edge("safety_check", END)
compiled_graph = graph.compile()
