from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class KitchenwareState(TypedDict):
    material: str
    max_temp: int
    is_compliant: bool

def validate_heat_resistance(state: KitchenwareState):
    state['is_compliant'] = state['max_temp'] >= 250
    return state

def check_material_safety(state: KitchenwareState):
    state['is_compliant'] = state['is_compliant'] and (state['material'] in ['aramid', 'silicone', 'cotton'])
    return state

graph = StateGraph(KitchenwareState)
graph.add_node("validate_temp", validate_heat_resistance)
graph.add_node("check_material", check_material_safety)
graph.add_edge("validate_temp", "check_material")
graph.add_edge("check_material", END)
graph.set_entry_point("validate_temp")
graph = graph.compile()
