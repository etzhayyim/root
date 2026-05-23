from typing import TypedDict
from langgraph.graph import StateGraph, END

class FileState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_load_capacity(state: FileState) -> FileState:
    capacity = state['specs'].get('load_capacity', 0)
    state['validated'] = capacity > 0
    if not state['validated']: state['error'] = 'Invalid load capacity'
    return state

def check_anti_tilt(state: FileState) -> FileState:
    state['validated'] = state['validated'] and state['specs'].get('anti_tilt', False)
    return state

graph = StateGraph(FileState)
graph.add_node('validate_load', validate_load_capacity)
graph.add_node('check_tilt', check_anti_tilt)
graph.add_edge('validate_load', 'check_tilt')
graph.add_edge('check_tilt', END)
graph.set_entry_point('validate_load')
