from typing import TypedDict
from langgraph.graph import StateGraph, END

class DiggingSpecState(TypedDict):
    depth: float
    soil_type: str
    is_approved: bool

def validate_depth(state: DiggingSpecState):
    state['is_approved'] = state['depth'] > 0 and state['depth'] <= 200
    return state

def check_soil_compatibility(state: DiggingSpecState):
    if state['soil_type'] == 'rocky':
        state['is_approved'] = False
    return state

graph = StateGraph(DiggingSpecState)
graph.add_node('validate', validate_depth)
graph.add_node('soil_check', check_soil_compatibility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'soil_check')
graph.add_edge('soil_check', END)
compile = graph.compile()