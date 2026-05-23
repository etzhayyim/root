from typing import TypedDict
from langgraph.graph import StateGraph, END

class AirCurtainState(TypedDict):
    width: float
    height: float
    velocity: float
    specs_verified: bool

def validate_specs(state: AirCurtainState):
    state['specs_verified'] = state['width'] > 0 and state['height'] > 0 and state['velocity'] >= 5.0
    return state

def route_verification(state: AirCurtainState):
    return 'verified' if state['specs_verified'] else 'failed'

graph = StateGraph(AirCurtainState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
