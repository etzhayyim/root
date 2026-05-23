from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    spec_data: dict
    validation_results: dict

def validate_material(state: PipeState):
    grade = state['spec_data'].get('grade')
    is_valid = grade in ['A106', 'A53', 'A333']
    return {'validation_results': {'material_ok': is_valid}}

def check_dimensions(state: PipeState):
    thickness = state['spec_data'].get('thickness', 0)
    return {'validation_results': {'thickness_compliant': thickness > 0}}

graph = StateGraph(PipeState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_dimensions', check_dimensions)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_dimensions')
graph.add_edge('check_dimensions', END)
graph = graph.compile()
