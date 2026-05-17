from typing import TypedDict
from langgraph.graph import StateGraph, END

class PrismState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: PrismState):
    required = ['surface_quality', 'coating', 'material']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def export_check(state: PrismState):
    # Simulate dual-use verification logic
    print('Checking export controls for prism grade...')
    return {'validation_passed': True}

graph = StateGraph(PrismState)
graph.add_node('validate', validate_specs)
graph.add_node('export_control', export_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_control')
graph.add_edge('export_control', END)
graph = graph.compile()