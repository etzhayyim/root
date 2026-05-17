from typing import TypedDict
from langgraph.graph import StateGraph, END

class RailCarState(TypedDict):
    capacity: float
    inspection_passed: bool
    logistics_approved: bool

def validate_cargo_load(state: RailCarState):
    state['inspection_passed'] = state['capacity'] <= 100.0
    return state

def approve_logistics(state: RailCarState):
    state['logistics_approved'] = True
    return state

graph = StateGraph(RailCarState)
graph.add_node('validate', validate_cargo_load)
graph.add_node('approve', approve_logistics)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()