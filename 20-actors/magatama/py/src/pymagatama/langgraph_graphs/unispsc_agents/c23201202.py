from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChassisState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_materials(state: ChassisState):
    # Simulate material compliance check
    state['validation_passed'] = 'material_cert' in state['specs']
    return state

def check_dimensions(state: ChassisState):
    # Simulate tolerance check
    if state['validation_passed']:
        state['validation_passed'] = 'tolerance' in state['specs']
    return state

graph = StateGraph(ChassisState)
graph.add_node('material_check', validate_materials)
graph.add_node('dimension_check', check_dimensions)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'dimension_check')
graph.add_edge('dimension_check', END)
app = graph.compile()