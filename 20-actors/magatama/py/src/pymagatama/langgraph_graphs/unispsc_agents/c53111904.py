from typing import TypedDict
from langgraph.graph import StateGraph, END

class ShoeProcureState(TypedDict):
    size: str
    material: str
    quality_score: float
    approved: bool

def validate_material(state: ShoeProcureState):
    state['approved'] = 'eco-friendly' in state['material'].lower()
    return state

def check_quality(state: ShoeProcureState):
    state['quality_score'] = 95.0 if state['approved'] else 50.0
    return state

graph = StateGraph(ShoeProcureState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_quality', check_quality)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_quality')
graph.add_edge('check_quality', END)
graph = graph.compile()
