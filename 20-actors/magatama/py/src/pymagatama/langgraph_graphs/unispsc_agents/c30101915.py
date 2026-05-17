from typing import TypedDict
from langgraph.graph import StateGraph, END

class CoilState(TypedDict):
    material: str
    diameter: float
    specs_verified: bool

def validate_plastic_coil(state: CoilState):
    is_valid = state['diameter'] > 0 and state['material'] in ['PVC', 'HDPE', 'PP']
    return {'specs_verified': is_valid}

graph = StateGraph(CoilState)
graph.add_node('validate', validate_plastic_coil)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()