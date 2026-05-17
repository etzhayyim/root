from typing import TypedDict
from langgraph.graph import StateGraph, END

class AbrasiveState(TypedDict):
    grit: int
    material: str
    is_compliant: bool

def validate_grit(state: AbrasiveState):
    state['is_compliant'] = state['grit'] >= 80
    return state

def check_material(state: AbrasiveState):
    valid_materials = ['Aluminum Oxide', 'Silicon Carbide']
    state['is_compliant'] = state['is_compliant'] and (state['material'] in valid_materials)
    return state

graph = StateGraph(AbrasiveState)
graph.add_node('validate_grit', validate_grit)
graph.add_node('check_material', check_material)
graph.set_entry_point('validate_grit')
graph.add_edge('validate_grit', 'check_material')
graph.add_edge('check_material', END)
graph = graph.compile()