from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    material_spec: dict
    validation_passed: bool

def validate_alloy_properties(state: ProcessingState):
    spec = state['material_spec']
    passed = 'copper_percentage' in spec and 'tin_percentage' in spec
    return {'validation_passed': passed}

def route_by_validation(state: ProcessingState):
    return 'process_order' if state['validation_passed'] else 'reject_order'

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_alloy_properties)
graph.add_node('process_order', lambda x: x)
graph.add_node('reject_order', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process_order', END)
graph.add_edge('reject_order', END)
graph = graph.compile()