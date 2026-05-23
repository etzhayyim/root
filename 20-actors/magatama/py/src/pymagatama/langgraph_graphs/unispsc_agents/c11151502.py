from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    purity: float
    origin: str
    is_verified: bool

def validate_mineral(state: MineralState):
    state['is_verified'] = state['purity'] >= 99.5
    return state

def route_mineral(state: MineralState):
    return 'verified' if state['is_verified'] else 'rejection'

graph = StateGraph(MineralState)
graph.add_node('validation', validate_mineral)
graph.add_edge('validation', END)
graph.set_entry_point('validation')
graph = graph.compile()
