from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CementSpec(TypedDict):
    strength: float
    dimensions: str
    is_compliant: bool

def validate_bricks(state: CementSpec):
    state['is_compliant'] = state['strength'] >= 15.0
    return state

graph = StateGraph(CementSpec)
graph.add_node('validate', validate_bricks)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()