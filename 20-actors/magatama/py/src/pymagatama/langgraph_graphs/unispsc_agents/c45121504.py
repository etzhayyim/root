from typing import TypedDict
from langgraph.graph import StateGraph, END

class CameraState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_camera_specs(state: CameraState):
    required = ['sensor_resolution_mp', 'video_codec_support']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def route_by_validation(state: CameraState):
    return 'valid' if state['validation_passed'] else 'invalid'

graph = StateGraph(CameraState)
graph.add_node('validator', validate_camera_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
graph.compile()
