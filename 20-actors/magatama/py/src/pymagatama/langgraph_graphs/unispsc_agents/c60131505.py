from typing import TypedDict
from langgraph.graph import StateGraph, END

class StandState(TypedDict):
    material: str
    stability_rating: float
    is_validated: bool

def validate_stability(state: StandState):
    state['is_validated'] = state['stability_rating'] > 8.0
    return state

def check_material(state: StandState):
    state['material'] = 'steel' if 'metal' in state['material'].lower() else 'plastic'
    return state

graph = StateGraph(StandState)
graph.add_node('check_material', check_material)
graph.add_node('validate_stability', validate_stability)
graph.set_entry_point('check_material')
graph.add_edge('check_material', 'validate_stability')
graph.add_edge('validate_stability', END)
graph = graph.compile()