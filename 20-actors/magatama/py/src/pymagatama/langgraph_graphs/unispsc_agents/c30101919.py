from typing import TypedDict
from langgraph.graph import StateGraph, END

class SteelState(TypedDict):
    material_type: str
    thickness_mm: float
    pattern_depth_mm: float
    inspection_passed: bool

def validate_specs(state: SteelState) -> SteelState:
    if state['thickness_mm'] > 0 and state['pattern_depth_mm'] > 0:
        state['inspection_passed'] = True
    return state

def check_surface(state: SteelState) -> SteelState:
    # Simulate surface consistency check
    return state

graph = StateGraph(SteelState)
graph.add_node('validate', validate_specs)
graph.add_node('surface_check', check_surface)
graph.set_entry_point('validate')
graph.add_edge('validate', 'surface_check')
graph.add_edge('surface_check', END)
graph = graph.compile()