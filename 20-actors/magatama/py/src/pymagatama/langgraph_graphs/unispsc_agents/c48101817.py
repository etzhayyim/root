from langgraph.graph import StateGraph, END
from typing import TypedDict

class CakeToolState(TypedDict):
    tool_id: str
    material_certified: bool
    thermal_rating: int
    is_approved: bool

def validate_material(state: CakeToolState):
    state['material_certified'] = True
    return 'check_thermal'

def check_thermal(state: CakeToolState):
    state['is_approved'] = state['thermal_rating'] > 100
    return 'end'

graph = StateGraph(CakeToolState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_thermal', check_thermal)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_thermal')
graph.add_edge('check_thermal', END)
compiled_graph = graph.compile()
