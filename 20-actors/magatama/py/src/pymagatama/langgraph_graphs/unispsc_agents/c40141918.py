from typing import TypedDict
from langgraph.graph import StateGraph, END

class DuctSpecState(TypedDict):
    material_compliance: bool
    pressure_test_passed: bool
    spec_validation_log: list

def validate_material(state: DuctSpecState):
    # Simulate material alloy validation logic
    state['material_compliance'] = True
    state['spec_validation_log'].append('Material chemistry validated.')
    return state

def perform_leak_test(state: DuctSpecState):
    # Simulate pressure/sealing test
    state['pressure_test_passed'] = True
    state['spec_validation_log'].append('Pressure leak test passed.')
    return state

graph = StateGraph(DuctSpecState)
graph.add_node('validate_material', validate_material)
graph.add_node('perform_leak_test', perform_leak_test)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'perform_leak_test')
graph.add_edge('perform_leak_test', END)
graph = graph.compile()
