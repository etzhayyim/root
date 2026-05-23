from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SweaterState(TypedDict):
    material: str
    quality_score: float
    compliant: bool

def validate_material(state: SweaterState) -> SweaterState:
    allowed_materials = ['wool', 'cotton', 'cashmere', 'polyester']
    state['compliant'] = state['material'].lower() in allowed_materials
    return state

def check_quality(state: SweaterState) -> SweaterState:
    state['quality_score'] = 1.0 if state['compliant'] else 0.0
    return state

graph = StateGraph(SweaterState)
graph.add_node('validate', validate_material)
graph.add_node('quality', check_quality)
graph.add_edge('validate', 'quality')
graph.add_edge('quality', END)
graph.set_entry_point('validate')
graph = graph.compile()
