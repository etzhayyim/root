from typing import TypedDict
from langgraph.graph import StateGraph, END

class PHState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: PHState):
    required = ['measurement_range', 'output_signal_type']
    missing = [f for f in required if f not in state['spec_data']]
    return {'validation_passed': len(missing) == 0, 'error_log': missing}

def route_by_validation(state: PHState):
    return 'process' if state['validation_passed'] else 'reject'

graph = StateGraph(PHState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()