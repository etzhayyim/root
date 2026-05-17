from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    machine_id: str
    spec_check: bool
    safety_compliance: bool

def validate_specs(state: ProcessingState):
    print(f"Validating specs for machine: {state['machine_id']}")
    return {"spec_check": True}

def check_safety(state: ProcessingState):
    print("Checking electrical and vibration safety standards.")
    return {"safety_compliance": True}

graph = StateGraph(ProcessingState)
graph.add_node("validate", validate_specs)
graph.add_node("safety", check_safety)
graph.add_edge("validate", "safety")
graph.add_edge("safety", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()