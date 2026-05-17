from typing import TypedDict
from langgraph.graph import StateGraph, END

class LightingState(TypedDict):
    spec_sheet: dict
    validation_passed: bool

def validate_optical_specs(state: LightingState):
    specs = state['spec_sheet']
    passed = specs.get('efficiency', 0) > 0.8 and bool(specs.get('certification'))
    return {'validation_passed': passed}

def route_by_validation(state: LightingState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(LightingState)
graph.add_node('validate', validate_optical_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': 'process', '__end__': END})
graph.add_node('process', lambda s: {'validation_passed': True})
graph.add_edge('process', END)
graph = graph.compile()