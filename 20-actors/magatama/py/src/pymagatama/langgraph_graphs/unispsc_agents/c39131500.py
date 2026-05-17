from typing import TypedDict
from langgraph.graph import StateGraph, END

class WireMarkerState(TypedDict):
    part_number: str
    material_spec: str
    validation_passed: bool

def validate_specs(state: WireMarkerState):
    # Simulate validation logic for wire marking material
    is_compliant = "UL94" in state.get("material_spec", "")
    return {"validation_passed": is_compliant}

def printer_setup(state: WireMarkerState):
    print(f"Configuring thermal transfer for {state['part_number']}")
    return {"validation_passed": True}

graph = StateGraph(WireMarkerState)
graph.add_node("validate", validate_specs)
graph.add_node("setup", printer_setup)
graph.set_entry_point("validate")
graph.add_edge("validate", "setup")
graph.add_edge("setup", END)
graph = graph.compile()