from typing import TypedDict
from langgraph.graph import StateGraph, END

class GlassSpecState(TypedDict):
    thickness: float
    fire_rated: bool
    dimensions: tuple
    is_compliant: bool

def validate_glass_specs(state: GlassSpecState):
    state['is_compliant'] = state['thickness'] >= 6.0 and state['fire_rated'] == True
    return state

graph = StateGraph(GlassSpecState)
graph.add_node('validator', validate_glass_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
compile_graph = graph.compile()