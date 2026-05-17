from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    spec_data: dict
    validation_results: dict

def validate_material(state: ExtrusionState):
    grade = state['spec_data'].get('material_grade')
    return {'validation_results': {'material_ok': grade is not None}}

def validate_geometry(state: ExtrusionState):
    tol = state['spec_data'].get('tolerance')
    return {'validation_results': {'geometry_ok': tol < 0.05}}

graph = StateGraph(ExtrusionState)
graph.add_node('material_check', validate_material)
graph.add_node('geometry_check', validate_geometry)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'geometry_check')
graph.add_edge('geometry_check', END)
graph = graph.compile()