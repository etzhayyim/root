from typing import TypedDict
from langgraph.graph import StateGraph, END

class SqueezerState(TypedDict):
    material: str
    is_food_safe: bool
    passed_qa: bool

def validate_materials(state: SqueezerState):
    state['is_food_safe'] = state['material'] in ['stainless_steel', 'food_grade_silicone']
    return state

def qc_inspection(state: SqueezerState):
    state['passed_qa'] = state['is_food_safe']
    return state

graph = StateGraph(SqueezerState)
graph.add_node('validate', validate_materials)
graph.add_node('qc', qc_inspection)
graph.add_edge('validate', 'qc')
graph.add_edge('qc', END)
graph.set_entry_point('validate')
graph = graph.compile()
