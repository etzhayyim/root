from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class CanvasState(TypedDict):
    dimensions: dict
    material: str
    is_validated: bool

def validate_specs(state: CanvasState):
    # Business logic for stretcher bar validation
    width = state['dimensions'].get('width', 0)
    state['is_validated'] = width > 0 and state['material'] in ['Pine', 'Aluminum']
    return state

graph = StateGraph(CanvasState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
