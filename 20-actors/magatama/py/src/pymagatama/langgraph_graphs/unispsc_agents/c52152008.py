from typing import TypedDict
from langgraph.graph import StateGraph, END

class KitchenwareState(TypedDict):
    material: str
    thermal_tolerance: int
    is_food_grade: bool
    approved: bool

def validate_material(state: KitchenwareState):
    # Business logic for material check
    state['approved'] = state['is_food_grade'] and state['thermal_tolerance'] > 90
    return state

builder = StateGraph(KitchenwareState)
builder.add_node('validation', validate_material)
builder.set_entry_point('validation')
builder.add_edge('validation', END)
graph = builder.compile()