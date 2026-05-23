from typing import TypedDict
from langgraph.graph import StateGraph, END

class ScaleState(TypedDict):
    capacity: float
    ip_rating: str
    is_calibrated: bool

def validate_specs(state: ScaleState):
    state['is_calibrated'] = state['capacity'] > 0 and state['ip_rating'] != ''
    return state

def route_verification(state: ScaleState):
    return 'verified' if state['is_calibrated'] else 'failed'

graph = StateGraph(ScaleState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
