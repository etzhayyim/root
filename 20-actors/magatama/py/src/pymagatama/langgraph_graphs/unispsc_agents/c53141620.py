from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    tool_id: str
    blade_sharpness: float
    has_safety_cover: bool
    approved: bool

def validate_blade_safety(state: ToolState):
    is_safe = state['has_safety_cover'] and (0.8 < state['blade_sharpness'] < 1.2)
    return {'approved': is_safe}

graph = StateGraph(ToolState)
graph.add_node('validate', validate_blade_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()