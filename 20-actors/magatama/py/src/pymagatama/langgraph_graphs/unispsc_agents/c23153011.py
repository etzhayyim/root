from typing import TypedDict
from langgraph.graph import StateGraph, END

class WeldingState(TypedDict):
    laser_power: float
    material_type: str
    validation_passed: bool

def validate_specs(state: WeldingState) -> WeldingState:
    state['validation_passed'] = state['laser_power'] > 0 and state['material_type'] != ""
    return state

def check_compliance(state: WeldingState) -> str:
    return "complete" if state['validation_passed'] else "error"

graph = StateGraph(WeldingState)
graph.add_node("validate", validate_specs)
graph.add_edge("validate", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()