from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PackagingState(TypedDict):
    material: str
    dimensions: dict
    approved: bool

def validate_materials(state: PackagingState):
    state['approved'] = state['material'] in ['plastic', 'metal', 'recycled_cardboard']
    return state

def check_dimensions(state: PackagingState):
    state['approved'] = state['approved'] and all(v > 0 for v in state['dimensions'].values())
    return state

graph = StateGraph(PackagingState)
graph.add_node('validate', validate_materials)
graph.add_node('dimensions', check_dimensions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'dimensions')
graph.add_edge('dimensions', END)
graph = graph.compile()
