from typing import TypedDict
from langgraph.graph import StateGraph, END

class FilmState(TypedDict):
    material_type: str
    thickness: float
    spec_compliant: bool

def validate_material(state: FilmState):
    valid_materials = ['acetate', 'vinyl', 'polyester']
    return {'spec_compliant': state['material_type'].lower() in valid_materials}

def check_safety(state: FilmState):
    return {'spec_compliant': state['spec_compliant'] and state['thickness'] > 0}

graph = StateGraph(FilmState)
graph.add_node('validate', validate_material)
graph.add_node('safety', check_safety)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()