from typing import TypedDict
from langgraph.graph import StateGraph, END

class InkState(TypedDict):
    viscosity: float
    cured: bool
    safety_verified: bool

def check_safety(state: InkState):
    state['safety_verified'] = True
    return state

def validate_viscosity(state: InkState):
    state['cured'] = state['viscosity'] > 0.5
    return state

graph = StateGraph(InkState)
graph.add_node('safety_check', check_safety)
graph.add_node('viscosity_check', validate_viscosity)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'viscosity_check')
graph.add_edge('viscosity_check', END)
graph = graph.compile()
