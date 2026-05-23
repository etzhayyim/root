from langgraph.graph import StateGraph, END
from typing import TypedDict

class StrainerState(TypedDict):
    mesh_size: int
    is_compatible: bool
    approved: bool

def validate_mesh(state: StrainerState):
    state['is_compatible'] = state['mesh_size'] > 0
    return state

def check_approval(state: StrainerState):
    state['approved'] = state['is_compatible']
    return state

graph = StateGraph(StrainerState)
graph.add_node('validate', validate_mesh)
graph.add_node('approval', check_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()
