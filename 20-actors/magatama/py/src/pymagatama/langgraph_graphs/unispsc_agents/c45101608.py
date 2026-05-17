from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ScreenState(TypedDict):
    mesh_count: int
    tension: float
    frame_material: str
    is_validated: bool

def validate_specs(state: ScreenState):
    # Business logic for silk screen procurement validation
    is_valid = state['mesh_count'] > 0 and state['tension'] > 20.0
    return {'is_validated': is_valid}

graph = StateGraph(ScreenState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()