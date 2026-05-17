from typing import TypedDict
from langgraph.graph import StateGraph, END

class MediaState(TypedDict):
    composition_data: dict
    validation_passed: bool

def validate_composition(state: MediaState):
    # Simulate chemical validation logic for media components
    passed = 'ph_level' in state['composition_data'] and state['composition_data']['ph_level'] <= 7.5
    return {'validation_passed': passed}

def route_by_validation(state: MediaState):
    return 'valid' if state['validation_passed'] else 'reject'

graph = StateGraph(MediaState)
graph.add_node('validate', validate_composition)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()