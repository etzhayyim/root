from typing import TypedDict
from langgraph.graph import StateGraph, END

class BodyBagState(TypedDict):
    spec_data: dict
    validation_results: dict

def validate_materials(state: BodyBagState):
    compliance = state['spec_data'].get('biohazard_compliant', False)
    return {'validation_results': {'is_safe': compliance}}

def check_dimensions(state: BodyBagState):
    size = state['spec_data'].get('length_cm', 0)
    return {'validation_results': {'is_valid_size': size > 200}}

graph = StateGraph(BodyBagState)
graph.add_node('material_check', validate_materials)
graph.add_node('dimension_check', check_dimensions)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'dimension_check')
graph.add_edge('dimension_check', END)
graph = graph.compile()