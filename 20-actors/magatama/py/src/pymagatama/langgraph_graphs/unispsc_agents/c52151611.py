from typing import TypedDict
from langgraph.graph import StateGraph, END

class KitchenwareState(TypedDict):
    material: str
    heat_resistance: int
    is_food_safe: bool

def validate_material(state: KitchenwareState):
    return {'is_food_safe': state['material'] in ['stainless_steel', 'silicone']}

def check_heat_threshold(state: KitchenwareState):
    print(f'Checking heat resistance for {state}')
    return {'heat_resistance': max(state['heat_resistance'], 200)}

graph = StateGraph(KitchenwareState)
graph.add_node('validate', validate_material)
graph.add_node('thermal_check', check_heat_threshold)
graph.add_edge('validate', 'thermal_check')
graph.add_edge('thermal_check', END)
graph.set_entry_point('validate')
app = graph.compile()