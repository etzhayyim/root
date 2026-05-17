from typing import TypedDict
from langgraph.graph import StateGraph, END

class RoofSystemState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_materials(state: RoofSystemState) -> RoofSystemState:
    # Simulate material compliance check for automotive roof
    state['validation_passed'] = 'material' in state['specs'] and state['specs']['material'] != 'incompatible'
    return state

def check_structural_load(state: RoofSystemState) -> RoofSystemState:
    # Simulate structural integrity compliance
    if state.get('validation_passed'):
        state['validation_passed'] = state['specs'].get('load_rating', 0) > 500
    return state

graph = StateGraph(RoofSystemState)
graph.add_node('validate', validate_materials)
graph.add_node('load_test', check_structural_load)
graph.add_edge('validate', 'load_test')
graph.add_edge('load_test', END)
graph.set_entry_point('validate')
graph = graph.compile()