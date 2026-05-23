from typing import TypedDict
from langgraph.graph import StateGraph, END

class StickerState(TypedDict):
    specs: dict
    approved: bool

def validate_dimensions(state: StickerState):
    width = state['specs'].get('width', 0)
    state['approved'] = width > 500
    return state

def check_material(state: StickerState):
    material = state['specs'].get('material', 'paper')
    state['approved'] = state['approved'] and (material != 'toxic_vinyl')
    return state

graph = StateGraph(StickerState)
graph.add_node('validate', validate_dimensions)
graph.add_node('material_check', check_material)
graph.set_entry_point('validate')
graph.add_edge('validate', 'material_check')
graph.add_edge('material_check', END)
graph = graph.compile()
