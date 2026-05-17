from typing import TypedDict
from langgraph.graph import StateGraph, END

class SpectrophotometerState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: SpectrophotometerState):
    required = ['wavelength_range_nm', 'photometric_accuracy']
    passed = all(k in state['spec_data'] for k in required)
    return {"validation_passed": passed}

def hardware_init(state: SpectrophotometerState):
    print("Initializing optical bench and light source...")
    return {}

graph = StateGraph(SpectrophotometerState)
graph.add_node("validate", validate_specs)
graph.add_node("init", hardware_init)
graph.add_edge("validate", "init")
graph.add_edge("init", END)
graph.set_entry_point("validate")
graph = graph.compile()