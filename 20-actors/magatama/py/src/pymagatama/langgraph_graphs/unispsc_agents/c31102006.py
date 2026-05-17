from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    material: str
    specs: dict
    approved: bool

def validate_material(state: CastingState):
    state['approved'] = 'aluminum_alloy' in state['material'].lower()
    return state

def check_quality(state: CastingState):
    state['approved'] = state['approved'] and state['specs'].get('tensile_strength', 0) > 200
    return state

graph = StateGraph(CastingState)
graph.add_node('validate', validate_material)
graph.add_node('quality', check_quality)
graph.add_edge('validate', 'quality')
graph.add_edge('quality', END)
graph.set_entry_point('validate')
graph = graph.compile()