from typing import TypedDict
from langgraph.graph import StateGraph, END

class DishwareState(TypedDict):
    material_spec: str
    is_food_grade: bool
    compliance_score: int

def validate_material(state: DishwareState):
    state['is_food_grade'] = 'SUS304' in state['material_spec']
    return state

def check_compliance(state: DishwareState):
    state['compliance_score'] = 100 if state['is_food_grade'] else 0
    return state

graph = StateGraph(DishwareState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()