from typing import TypedDict
from langgraph.graph import StateGraph, END

class AnesthesiaTubeState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_tube_specs(state: AnesthesiaTubeState):
    required = ['iso_certified', 'material_grade']
    state['is_compliant'] = all(k in state['spec_data'] for k in required)
    return state

def check_pressure(state: AnesthesiaTubeState):
    pressure = state['spec_data'].get('pressure_rating', 0)
    state['is_compliant'] = state['is_compliant'] and (pressure >= 50)
    return state

graph = StateGraph(AnesthesiaTubeState)
graph.add_node("validate", validate_tube_specs)
graph.add_node("pressure_check", check_pressure)
graph.add_edge("validate", "pressure_check")
graph.add_edge("pressure_check", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()
