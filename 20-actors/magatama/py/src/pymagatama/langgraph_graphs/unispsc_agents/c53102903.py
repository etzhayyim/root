from typing import TypedDict
from langgraph.graph import StateGraph, END

class ClothingState(TypedDict):
    spec_data: dict
    approved: bool

def validate_materials(state: ClothingState):
    materials = state['spec_data'].get('materials', [])
    is_safe = all(m in ['polyester', 'cotton', 'spandex'] for m in materials)
    return {'approved': is_safe}

def final_check(state: ClothingState):
    return {'approved': state['approved'] and state['spec_data'].get('flammability_test', False)}

graph = StateGraph(ClothingState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('final_check', final_check)
graph.set_entry_point('validate_materials')
graph.add_edge('validate_materials', 'final_check')
graph.add_edge('final_check', END)
graph = graph.compile()