from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WindowState(TypedDict):
    dimensions: dict
    material: str
    compliance_check: bool
    validation_logs: List[str]

def validate_dimensions(state: WindowState):
    width = state['dimensions'].get('width', 0)
    height = state['dimensions'].get('height', 0)
    is_valid = 500 < width < 3000 and 500 < height < 3000
    return {'compliance_check': is_valid, 'validation_logs': ['Dimensions checked']}

def check_material_specs(state: WindowState):
    valid_materials = ['aluminum', 'vinyl', 'wood', 'fiberglass']
    return {'compliance_check': state['material'] in valid_materials, 'validation_logs': state['validation_logs'] + ['Material checked']}

graph = StateGraph(WindowState)
graph.add_node('validate', validate_dimensions)
graph.add_node('spec_review', check_material_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', 'spec_review')
graph.add_edge('spec_review', END)
graph = graph.compile()