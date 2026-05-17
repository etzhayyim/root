from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ClutchSpecState(TypedDict):
    part_id: str
    material: str
    tolerances: float
    qc_passed: bool

def validate_materials(state: ClutchSpecState):
    allowed = ['ADC12', 'A380']
    return {'qc_passed': state['material'] in allowed}

def check_dimensions(state: ClutchSpecState):
    return {'qc_passed': state['tolerances'] <= 0.05}

graph = StateGraph(ClutchSpecState)
graph.add_node('validate', validate_materials)
graph.add_node('check_dims', check_dimensions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_dims')
graph.add_edge('check_dims', END)
graph = graph.compile()