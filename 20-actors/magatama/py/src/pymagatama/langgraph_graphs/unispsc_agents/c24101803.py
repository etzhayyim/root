from typing import TypedDict
from langgraph.graph import StateGraph, END

class DockRampState(TypedDict):
    load_capacity: float
    safety_approved: bool
    inspection_status: str

def validate_load_capacity(state: DockRampState):
    state['load_capacity_ok'] = state['load_capacity'] > 0
    return state

def verify_safety(state: DockRampState):
    state['safety_approved'] = True
    return state

graph = StateGraph(DockRampState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('safety', verify_safety)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
