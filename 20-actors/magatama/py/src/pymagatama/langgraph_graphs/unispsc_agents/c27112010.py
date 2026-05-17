from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    tool_type: str
    material: str
    inspection_passed: bool

def validate_materials(state: ToolState):
    state['inspection_passed'] = state['material'] in ['carbon_steel', 'stainless_steel']
    return state

def check_dimensions(state: ToolState):
    return state

graph = StateGraph(ToolState)
graph.add_node('validate', validate_materials)
graph.add_node('measure', check_dimensions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'measure')
graph.add_edge('measure', END)
graph = graph.compile()