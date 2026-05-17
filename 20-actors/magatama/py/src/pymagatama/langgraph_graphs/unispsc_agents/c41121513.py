from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipetteState(TypedDict):
    material: str
    volume: float
    verified: bool

def validate_material(state: PipetteState):
    valid_materials = ['borosilicate', 'polypropylene']
    return {'verified': state['material'] in valid_materials}

def route_quality(state: PipetteState):
    return 'passed' if state['verified'] else 'failed'

graph = StateGraph(PipetteState)
graph.add_node('validation', validate_material)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph.compile()