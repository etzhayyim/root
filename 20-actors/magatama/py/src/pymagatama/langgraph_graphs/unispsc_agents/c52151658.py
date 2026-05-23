from typing import TypedDict
from langgraph.graph import StateGraph, END

class DoughKnifeState(TypedDict):
    spec_data: dict
    validated: bool

def validate_food_grade(state: DoughKnifeState):
    material = state['spec_data'].get('material', '')
    return {'validated': material in ['SS304', 'SS316', 'Food-Grade Plastic']}

graph = StateGraph(DoughKnifeState)
graph.add_node('validate', validate_food_grade)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
