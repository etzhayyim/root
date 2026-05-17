from langgraph.graph import StateGraph, END
from typing import TypedDict

class BoardState(TypedDict):
    spec: dict
    approved: bool

def validate_dimensions(state: BoardState):
    width = state['spec'].get('width', 0)
    height = state['spec'].get('height', 0)
    return {'approved': width > 0 and height > 0}

graph = StateGraph(BoardState)
graph.add_node('validate', validate_dimensions)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()