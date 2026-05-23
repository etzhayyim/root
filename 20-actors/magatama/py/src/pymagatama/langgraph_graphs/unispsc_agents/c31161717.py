from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WingNutState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_material(state: WingNutState):
    material = state.get('spec_data', {}).get('material', '').lower()
    if not material:
        state['validation_errors'].append('Material specification missing')
    return state

def check_dimensions(state: WingNutState):
    diameter = state.get('spec_data', {}).get('diameter', 0)
    if diameter <= 0:
        state['validation_errors'].append('Invalid diameter specified')
    return state

def finalize_check(state: WingNutState):
    state['is_approved'] = len(state.get('validation_errors', [])) == 0
    return state

graph = StateGraph(WingNutState)
graph.add_node('material_check', validate_material)
graph.add_node('dimension_check', check_dimensions)
graph.add_node('finalizer', finalize_check)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'dimension_check')
graph.add_edge('dimension_check', 'finalizer')
graph.add_edge('finalizer', END)
