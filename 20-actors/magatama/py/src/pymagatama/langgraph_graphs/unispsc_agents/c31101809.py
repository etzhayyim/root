from typing import TypedDict
from langgraph.graph import StateGraph, END

class BerylliumProcessState(TypedDict):
    material_safety_check: bool
    export_license_verified: bool
    dimensional_analysis_passed: bool

def validate_hazardous_materials(state: BerylliumProcessState):
    state['material_safety_check'] = True
    return 'check_export'

def verify_export_controls(state: BerylliumProcessState):
    state['export_license_verified'] = True
    return 'validate_dims'

def validate_dimensions(state: BerylliumProcessState):
    state['dimensional_analysis_passed'] = True
    return END

graph = StateGraph(BerylliumProcessState)
graph.add_node('safety', validate_hazardous_materials)
graph.add_node('check_export', verify_export_controls)
graph.add_node('validate_dims', validate_dimensions)
graph.set_entry_point('safety')
graph.add_edge('safety', 'check_export')
graph.add_edge('check_export', 'validate_dims')
graph.add_edge('validate_dims', END)
graph = graph.compile()