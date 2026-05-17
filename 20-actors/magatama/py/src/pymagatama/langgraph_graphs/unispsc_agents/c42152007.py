from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalState(TypedDict):
    device_id: str
    validation_passed: bool
    rad_compliance: bool

def validate_radiation_safety(state: DentalState) -> DentalState:
    print(f"Validating radiation compliance for unit {state['device_id']}")
    state['rad_compliance'] = True
    return state

def check_image_fidelity(state: DentalState) -> DentalState:
    print("Running image contrast and fidelity check...")
    state['validation_passed'] = True
    return state

graph = StateGraph(DentalState)
graph.add_node("radiation_check", validate_radiation_safety)
graph.add_node("fidelity_check", check_image_fidelity)
graph.set_entry_point("radiation_check")
graph.add_edge("radiation_check", "fidelity_check")
graph.add_edge("fidelity_check", END)
graph = graph.compile()