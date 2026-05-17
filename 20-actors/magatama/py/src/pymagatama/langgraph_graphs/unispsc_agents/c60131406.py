from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class XylophoneState(TypedDict):
    spec_data: dict
    validation_passed: bool
    inspection_report: str

def validate_pitch(state: XylophoneState):
    pitch = state['spec_data'].get('frequency', 440)
    state['validation_passed'] = 439 <= pitch <= 441
    state['inspection_report'] = 'Pitch verified' if state['validation_passed'] else 'Pitch out of tolerance'
    return state

def check_material(state: XylophoneState):
    material = state['spec_data'].get('wood_type', 'rosewood')
    state['validation_passed'] = state['validation_passed'] and (material in ['rosewood', 'padauk'])
    return state

graph = StateGraph(XylophoneState)
graph.add_node('validate_pitch', validate_pitch)
graph.add_node('check_material', check_material)
graph.set_entry_point('validate_pitch')
graph.add_edge('validate_pitch', 'check_material')
graph.add_edge('check_material', END)
graph = graph.compile()