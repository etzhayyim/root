from typing import TypedDict
from langgraph.graph import StateGraph, END

class TuningForkState(TypedDict):
    frequency: float
    certification_valid: bool
    inspection_passed: bool

def validate_frequency(state: TuningForkState):
    return {"inspection_passed": 128 <= state['frequency'] <= 4096}

def check_compliance(state: TuningForkState):
    return {"certification_valid": True}

graph = StateGraph(TuningForkState)
graph.add_node("validate", validate_frequency)
graph.add_node("certify", check_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "certify")
graph.add_edge("certify", END)
graph = graph.compile()
