from typing import TypedDict
from langgraph.graph import StateGraph, END

class LaserProcState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_safety_protocols(state: LaserProcState):
    laser_class = state['specs'].get('laser_class', 0)
    state['is_compliant'] = laser_class <= 4
    return state

def check_export_controls(state: LaserProcState):
    return state

graph = StateGraph(LaserProcState)
graph.add_node('safety_check', validate_safety_protocols)
graph.add_node('export_check', check_export_controls)
graph.add_edge('safety_check', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('safety_check')
graph = graph.compile()
