from typing import TypedDict
from langgraph.graph import StateGraph, END

class KitchenwareState(TypedDict):
    material: str
    volume: float
    has_coating: bool
    approved: bool

def validate_materials(state: KitchenwareState):
    # Ensuring food-grade material compliance
    state['approved'] = state['material'] in ['cast_iron', 'enameled_steel', 'aluminum']
    return state

def check_capacity(state: KitchenwareState):
    # Logical validation for domestic kitchenware capacity
    if state['volume'] > 20: state['approved'] = False
    return state

graph = StateGraph(KitchenwareState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_capacity', check_capacity)
graph.set_entry_point('validate_materials')
graph.add_edge('validate_materials', 'check_capacity')
graph.add_edge('check_capacity', END)
graph = graph.compile()