from typing import TypedDict
from langgraph.graph import StateGraph, END

class AccelerometerState(TypedDict):
    spec_data: dict
    validation_results: dict

def validate_specs(state: AccelerometerState):
    # Business logic for confirming sensitivity and G-range requirements
    is_valid = state['spec_data'].get('sensitivity_range_g', 0) > 0
    return {'validation_results': {'is_valid': is_valid}}

def export_control_check(state: AccelerometerState):
    # Check for dual-use high-g specifications
    is_restricted = state['spec_data'].get('sensitivity_range_g', 0) > 50
    return {'validation_results': {'restricted': is_restricted}}

graph = StateGraph(AccelerometerState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', export_control_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()