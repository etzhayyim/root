from typing import TypedDict
from langgraph.graph import StateGraph, END

class ShelfLinerState(TypedDict):
    material: str
    dimensions: dict
    is_compliant: bool

def validate_material(state: ShelfLinerState):
    state['is_compliant'] = state['material'] in ['PVC', 'EVA', 'Silicone']
    return state

def check_dimensions(state: ShelfLinerState):
    if state['dimensions'].get('width', 0) > 0:
        print('Dimensions verified')
    return state

graph = StateGraph(ShelfLinerState)
graph.add_node('validate', validate_material)
graph.add_node('check_dims', check_dimensions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_dims')
graph.add_edge('check_dims', END)
graph = graph.compile()