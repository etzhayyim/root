from typing import TypedDict
from langgraph.graph import StateGraph, END

class MacrameState(TypedDict):
    spec_data: dict
    validation_report: list

def validate_materials(state: MacrameState):
    material = state['spec_data'].get('Material Composition')
    is_valid = material in ['Cotton', 'Jute', 'Recycled Polyester']
    return {'validation_report': [f'Material validation: {is_valid}']}

def check_dimensions(state: MacrameState):
    diameter = state['spec_data'].get('Diameter (mm)', 0)
    error = 'Invalid diameter' if diameter <= 0 else None
    return {'validation_report': [error] if error else ['Diameter pass']}

graph = StateGraph(MacrameState)
graph.add_node('validate', validate_materials)
graph.add_node('dimension', check_dimensions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'dimension')
graph.add_edge('dimension', END)
graph = graph.compile()
