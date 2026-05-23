from typing import TypedDict
from langgraph.graph import StateGraph, END

class BushingState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_dimensions(state: BushingState):
    # Business logic for tolerance checking
    tolerance = state['spec_data'].get('tolerance', 0.01)
    passed = tolerance <= 0.05
    return {'validation_passed': passed}

def check_material(state: BushingState):
    # Ensure material meets industrial standards
    return {'validation_passed': state['validation_passed'] and 'steel' in state['spec_data'].get('material', '').lower()}

graph = StateGraph(BushingState)
graph.add_node('validate_dim', validate_dimensions)
graph.add_node('check_mat', check_material)
graph.set_entry_point('validate_dim')
graph.add_edge('validate_dim', 'check_mat')
graph.add_edge('check_mat', END)
graph = graph.compile()
