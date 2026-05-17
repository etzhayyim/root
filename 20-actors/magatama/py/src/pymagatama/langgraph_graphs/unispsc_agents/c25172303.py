from typing import TypedDict
from langgraph.graph import StateGraph, END

class WindowState(TypedDict):
    part_number: str
    material_spec: str
    safety_rating: bool
    approved: bool

def validate_glass(state: WindowState) -> WindowState:
    state['approved'] = state['safety_rating'] and len(state['material_spec']) > 0
    return state

workflow = StateGraph(WindowState)
workflow.add_node('validation', validate_glass)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()