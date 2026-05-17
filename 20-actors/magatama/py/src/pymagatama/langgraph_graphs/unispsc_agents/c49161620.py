from typing import TypedDict
from langgraph.graph import StateGraph, END

class GripState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_materials(state: GripState):
    required = ['material_composition', 'thickness_mm']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def process_grip_order(state: GripState):
    print('Processing racquet grip specifications...')
    return {'validation_passed': True}

graph = StateGraph(GripState)
graph.add_node('validate', validate_materials)
graph.add_node('process', process_grip_order)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()