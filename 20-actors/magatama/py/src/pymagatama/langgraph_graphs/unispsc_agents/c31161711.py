from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class EyeNutState(TypedDict):
    part_number: str
    material_certified: bool
    load_test_passed: bool
    errors: List[str]

def validate_material(state: EyeNutState):
    if not state.get('material_certified', False):
        state['errors'].append('Material certification missing')
    return state

def validate_load_capacity(state: EyeNutState):
    if not state.get('load_test_passed', False):
        state['errors'].append('Load test validation failed')
    return state

graph = StateGraph(EyeNutState)
graph.add_node('material_check', validate_material)
graph.add_node('load_check', validate_load_capacity)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'load_check')
graph.add_edge('load_check', END)
graph = graph.compile()
