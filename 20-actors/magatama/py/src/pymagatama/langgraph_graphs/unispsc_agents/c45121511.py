from typing import TypedDict
from langgraph.graph import StateGraph, END

class CameraState(TypedDict):
    spec_data: dict
    is_compliant: bool
    export_rating: str

def validate_specs(state: CameraState):
    fps = state['spec_data'].get('fps', 0)
    state['is_compliant'] = fps > 1000
    return state

def check_export_controls(state: CameraState):
    state['export_rating'] = 'ECCN-6A003' if state['spec_data'].get('fps', 0) > 5000 else 'None'
    return state

graph = StateGraph(CameraState)
graph.add_node('validate', validate_specs)
graph.add_node('export', check_export_controls)
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph.set_entry_point('validate')
graph = graph.compile()