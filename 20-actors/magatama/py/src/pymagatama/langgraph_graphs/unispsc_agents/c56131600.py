from typing import TypedDict
from langgraph.graph import StateGraph, END

class DisplaySpecState(TypedDict):
    dimensions: dict
    material_certified: bool
    stability_test_passed: bool
    approved: bool

def validate_dimensions(state: DisplaySpecState) -> DisplaySpecState:
    # Simplified mock validation logic for display footprint
    state['approved'] = state['dimensions'].get('height', 0) < 250
    return state

def check_safety_compliance(state: DisplaySpecState) -> DisplaySpecState:
    if state['material_certified'] and state['stability_test_passed']:
        state['approved'] = True
    else:
        state['approved'] = False
    return state

graph = StateGraph(DisplaySpecState)
graph.add_node('validate_dims', validate_dimensions)
graph.add_node('safety_check', check_safety_compliance)
graph.set_entry_point('validate_dims')
graph.add_edge('validate_dims', 'safety_check')
graph.add_edge('safety_check', END)
graph = graph.compile()
