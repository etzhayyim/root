from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FrameState(TypedDict):
    frame_type: str
    material_check: bool
    dimensions: dict
    approved: bool

def validate_materials(state: FrameState):
    # Simulate material compliance check for plastics
    state['material_check'] = True
    return state

def check_dimensions(state: FrameState):
    # Validate dimensions against procurement specs
    state['approved'] = state['dimensions'].get('width', 0) > 0
    return state

graph = StateGraph(FrameState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_dimensions', check_dimensions)
graph.set_entry_point('validate_materials')
graph.add_edge('validate_materials', 'check_dimensions')
graph.add_edge('check_dimensions', END)
graph = graph.compile()
