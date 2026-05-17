from typing import TypedDict
from langgraph.graph import StateGraph, END

class IrisState(TypedDict):
    diameter: float
    material: str
    is_validated: bool

def validate_specs(state: IrisState):
    state['is_validated'] = state['diameter'] > 0 and state['material'] != ''
    return state

def build_graph():
    graph = StateGraph(IrisState)
    graph.add_node('validate', validate_specs)
    graph.set_entry_point('validate')
    graph.add_edge('validate', END)
    return graph.compile()

graph = build_graph()