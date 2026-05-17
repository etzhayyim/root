from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProfileState(TypedDict):
    material: str
    dimensions: dict
    approved: bool

def validate_material(state: ProfileState):
    state['approved'] = state['material'] in ['Aluminum', 'Steel', 'PVC']
    return state

def check_dimensions(state: ProfileState):
    if state['approved']:
        state['approved'] = all(val > 0 for val in state['dimensions'].values())
    return state

graph = StateGraph(ProfileState)
graph.add_node('validate', validate_material)
graph.add_node('dimensions', check_dimensions)
graph.add_edge('validate', 'dimensions')
graph.add_edge('dimensions', END)
graph.set_entry_point('validate')
graph = graph.compile()