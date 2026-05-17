from typing import TypedDict
from langgraph.graph import StateGraph, END

class CameraState(TypedDict):
    spec_data: dict
    validation_score: float
    is_compliant: bool

def validate_specs(state: CameraState) -> CameraState:
    # Logic for offset camera spec validation
    state['is_compliant'] = state['spec_data'].get('resolution', 0) >= 600
    return state

def check_export_control(state: CameraState) -> CameraState:
    # Logic for dual-use export control check
    state['validation_score'] = 0.95 if state['is_compliant'] else 0.0
    return state

graph = StateGraph(CameraState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export_control)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
graph = graph.compile()