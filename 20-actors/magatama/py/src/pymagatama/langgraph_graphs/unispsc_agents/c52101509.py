from typing import TypedDict
from langgraph.graph import StateGraph, END

class MatState(TypedDict):
    spec: dict
    approved: bool

def validate_material(state: MatState) -> MatState:
    material = state['spec'].get('material', '')
    state['approved'] = material in ['Polyester', 'Rubber', 'Cotton']
    return state

def check_dimensions(state: MatState) -> MatState:
    if state['approved']:
        width = state['spec'].get('width', 0)
        state['approved'] = 0 < width < 500
    return state

graph = StateGraph(MatState)
graph.add_node('validate', validate_material)
graph.add_node('dimensions', check_dimensions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'dimensions')
graph.add_edge('dimensions', END)
app = graph.compile()