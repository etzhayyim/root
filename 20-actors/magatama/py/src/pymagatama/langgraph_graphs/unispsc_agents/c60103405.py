from typing import TypedDict
from langgraph.graph import StateGraph, END

class RackState(TypedDict):
    dimensions: dict
    material: str
    is_validated: bool

def validate_specs(state: RackState):
    width = state['dimensions'].get('width', 0)
    state['is_validated'] = width > 0 and state['material'] != ''
    return state

graph = StateGraph(RackState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()