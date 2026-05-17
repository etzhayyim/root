from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class JewelryState(TypedDict):
    material: str
    quality_score: float
    verified: bool

def validate_material(state: JewelryState):
    state['verified'] = state['material'] in ['Gold', 'Silver', 'Platinum']
    return state

def check_quality(state: JewelryState):
    state['quality_score'] = 1.0 if state['verified'] else 0.0
    return state

graph = StateGraph(JewelryState)
graph.add_node('validate', validate_material)
graph.add_node('quality', check_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', 'quality')
graph.add_edge('quality', END)
graph = graph.compile()