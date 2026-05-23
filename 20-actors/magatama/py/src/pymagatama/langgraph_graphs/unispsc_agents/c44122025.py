from typing import TypedDict
from langgraph.graph import StateGraph, END

class BinderState(TypedDict):
    material: str
    hole_consistency: bool
    is_compliant: bool

def check_material(state: BinderState):
    # Validate if material satisfies office environmental standards
    state['is_compliant'] = state['material'] in ['Polypropylene', 'PVC-Free']
    return state

def validate_format(state: BinderState):
    # Ensure holes are compatible with standard binder mechanisms
    state['is_compliant'] = state['is_compliant'] and state['hole_consistency']
    return state

graph = StateGraph(BinderState)
graph.add_node('check_material', check_material)
graph.add_node('validate_format', validate_format)
graph.set_entry_point('check_material')
graph.add_edge('check_material', 'validate_format')
graph.add_edge('validate_format', END)
graph = graph.compile()
