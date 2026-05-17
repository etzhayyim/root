from typing import TypedDict
from langgraph.graph import StateGraph, END

class WireState(TypedDict):
    diameter: float
    coating_mass: float
    specification_compliant: bool

def validate_specs(state: WireState):
    state['specification_compliant'] = (state['diameter'] > 0 and state['coating_mass'] >= 200)
    return state

graph = StateGraph(WireState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()