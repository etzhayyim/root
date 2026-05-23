from typing import TypedDict
from langgraph.graph import StateGraph, END

class DriveState(TypedDict):
    capacity: float
    compatibility: str
    validation_status: bool

def validate_drive_spec(state: DriveState):
    state['validation_status'] = state['capacity'] >= 1.0
    return state

def check_compatibility(state: DriveState):
    state['compatibility'] = 'Validated' if state['validation_status'] else 'Invalid'
    return state

graph = StateGraph(DriveState)
graph.add_node('validate', validate_drive_spec)
graph.add_node('check', check_compatibility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check')
graph.add_edge('check', END)
graph = graph.compile()
