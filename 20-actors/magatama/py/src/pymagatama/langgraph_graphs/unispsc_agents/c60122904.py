from typing import TypedDict
from langgraph.graph import StateGraph, END

class CraftState(TypedDict):
    material: str
    quality_score: float
    inspection_passed: bool

def validate_material(state: CraftState) -> CraftState:
    state['inspection_passed'] = state['material'] == 'straw'
    return state

def check_quality(state: CraftState) -> CraftState:
    state['quality_score'] = 1.0 if state['inspection_passed'] else 0.0
    return state

graph = StateGraph(CraftState)
graph.add_node('validate', validate_material)
graph.add_node('quality', check_quality)
graph.add_edge('validate', 'quality')
graph.add_edge('quality', END)
graph.set_entry_point('validate')
graph = graph.compile()