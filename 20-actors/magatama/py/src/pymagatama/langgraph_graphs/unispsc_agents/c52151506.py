from typing import TypedDict
from langgraph.graph import StateGraph, END

class ContainerState(TypedDict):
    material: str
    is_food_grade: bool
    thermal_rating: int

def validate_material(state: ContainerState):
    allowed = ['PET', 'PP', 'Paper', 'PLA']
    return {'is_food_grade': state['material'] in allowed}

def check_thermal(state: ContainerState):
    return {'thermal_rating': max(state['thermal_rating'], 0)}

graph = StateGraph(ContainerState)
graph.add_node('validate', validate_material)
graph.add_node('thermal', check_thermal)
graph.add_edge('validate', 'thermal')
graph.add_edge('thermal', END)
graph.set_entry_point('validate')
graph = graph.compile()