from typing import TypedDict
from langgraph.graph import StateGraph, END

class ScreenState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_screen_specs(state: ScreenState):
    required = ['mesh_size', 'flow_capacity']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def route_by_validation(state: ScreenState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(ScreenState)
graph.add_node('validate', validate_screen_specs)
graph.add_node('process', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()
