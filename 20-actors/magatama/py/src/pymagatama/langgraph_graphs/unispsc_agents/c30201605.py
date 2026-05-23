from typing import TypedDict
from langgraph.graph import StateGraph, END

class GazeboState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_structural_integrity(state: GazeboState):
    state['is_compliant'] = state['specs'].get('wind_load', 0) > 50
    return state

def approve_procurement(state: GazeboState):
    print('Gazebo order verified for safety.')
    return state

graph = StateGraph(GazeboState)
graph.add_node('validate', validate_structural_integrity)
graph.add_node('approve', approve_procurement)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
