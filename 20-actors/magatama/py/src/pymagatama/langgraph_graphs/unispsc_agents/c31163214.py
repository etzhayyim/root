from typing import TypedDict
from langgraph.graph import StateGraph, END

class ShearPinState(TypedDict):
    material_certified: bool
    shear_test_results: float
    status: str

def validate_material(state: ShearPinState):
    return {'material_certified': True}

def perform_shear_test(state: ShearPinState):
    return {'status': 'PASSED' if state['shear_test_results'] > 500 else 'FAILED'}

graph = StateGraph(ShearPinState)
graph.add_node('validate', validate_material)
graph.add_node('test', perform_shear_test)
graph.set_entry_point('validate')
graph.add_edge('validate', 'test')
graph.add_edge('test', END)
graph = graph.compile()