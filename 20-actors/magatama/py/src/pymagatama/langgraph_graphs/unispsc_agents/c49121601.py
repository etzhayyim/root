from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CampingGearState(TypedDict):
    product_id: str
    specs: dict
    approved: bool

def validate_load_capacity(state: CampingGearState):
    load = state['specs'].get('load_capacity', 0)
    state['approved'] = load >= 100
    return state

def check_material_safety(state: CampingGearState):
    material = state['specs'].get('material', '')
    if 'flame_retardant' not in material:
        state['approved'] = False
    return state

graph = StateGraph(CampingGearState)
graph.add_node('validate_load', validate_load_capacity)
graph.add_node('safety_check', check_material_safety)
graph.add_edge('validate_load', 'safety_check')
graph.add_edge('safety_check', END)
graph.set_entry_point('validate_load')
graph = graph.compile()