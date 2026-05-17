from typing import TypedDict
from langgraph.graph import StateGraph, END

class WireState(TypedDict):
    diameter: float
    conductivity: float
    compliant: bool

def validate_specs(state: WireState):
    state['compliant'] = state['diameter'] > 0 and state['conductivity'] > 0.6
    return state

graph = StateGraph(WireState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()