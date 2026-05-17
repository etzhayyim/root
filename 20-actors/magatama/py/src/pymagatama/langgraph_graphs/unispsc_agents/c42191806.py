from langgraph.graph import StateGraph, END
from typing import TypedDict

class TrapezeState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_load_capacity(state: TrapezeState):
    load = state['spec_data'].get('load_capacity', 0)
    is_valid = load >= 150  # Standard clinical requirement
    return {'validated': is_valid, 'error_log': [] if is_valid else ['Insufficient load capacity']}

def check_compatibility(state: TrapezeState):
    compatible = state['spec_data'].get('bed_frame_fit', False)
    return {'validated': state['validated'] and compatible}

graph = StateGraph(TrapezeState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('check_fit', check_compatibility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_fit')
graph.add_edge('check_fit', END)
graph = graph.compile()