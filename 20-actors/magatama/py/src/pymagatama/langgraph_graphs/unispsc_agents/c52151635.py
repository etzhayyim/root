from typing import TypedDict
from langgraph.graph import StateGraph, END

class KitchenwareState(TypedDict):
    material: str
    food_grade_certified: bool
    is_approved: bool

def validate_material(state: KitchenwareState):
    return {'is_approved': state['material'] == 'Stainless Steel 304' and state['food_grade_certified']}

graph = StateGraph(KitchenwareState)
graph.add_node('validate', validate_material)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
