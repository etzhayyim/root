from typing import TypedDict
from langgraph.graph import StateGraph, END

class CameraSpecState(TypedDict):
    resolution: int
    interface: str
    is_compliant: bool

def validate_camera_specs(state: CameraSpecState):
    state['is_compliant'] = state['resolution'] >= 1200 and state['interface'] in ['MIPI', 'USB3.0']
    return state

def routing_logic(state: CameraSpecState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(CameraSpecState)
graph.add_node('validate', validate_camera_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()