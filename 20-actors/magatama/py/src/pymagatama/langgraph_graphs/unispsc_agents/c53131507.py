from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ToothpickState(TypedDict):
    material: str
    quality_score: float
    inspection_passed: bool

def validate_materials(state: ToothpickState):
    state['inspection_passed'] = state['material'] in ['Wood', 'Bamboo']
    return state

def check_quality(state: ToothpickState):
    state['quality_score'] = 1.0 if state['inspection_passed'] else 0.0
    return state

graph = StateGraph(ToothpickState)
graph.add_node('validate', validate_materials)
graph.add_node('quality', check_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', 'quality')
graph.add_edge('quality', END)
graph = graph.compile()