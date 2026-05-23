from typing import TypedDict
from langgraph.graph import StateGraph, END

class PotatoMasherState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_materials(state: PotatoMasherState):
    is_food_safe = state['specs'].get('food_grade') == True
    return {'validation_passed': is_food_safe}

graph = StateGraph(PotatoMasherState)
graph.add_node('validate', validate_materials)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
