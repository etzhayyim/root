from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HardwareState(TypedDict):
    load_capacity: float
    surface_type: str
    is_approved: bool

def validate_load(state: HardwareState):
    state['is_approved'] = state['load_capacity'] > 0 and state['surface_type'] != ''
    return state

graph = StateGraph(HardwareState)
graph.add_node('validation', validate_load)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()