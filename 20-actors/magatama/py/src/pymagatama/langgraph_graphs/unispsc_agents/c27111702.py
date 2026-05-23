from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ToolSpecState(TypedDict):
    tool_id: str
    specs: dict
    validated: bool

def validate_spec(state: ToolSpecState):
    # Simulate CAD/Spec validation logic for nut drivers
    required = ['tip_size_mm', 'material_composition']
    state['validated'] = all(k in state['specs'] for k in required)
    return state

def route_by_validation(state: ToolSpecState):
    return 'valid' if state['validated'] else 'invalid'

graph = StateGraph(ToolSpecState)
graph.add_node('validator', validate_spec)
graph.add_edge('validator', END)
graph.set_entry_point('validator')
graph = graph.compile()
