from typing import TypedDict
from langgraph.graph import StateGraph, END

class CompressorState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_logs: list

def validate_specs(state: CompressorState):
    specs = state['spec_data']
    logs = []
    if specs.get('pressure', 0) > 1000:
        logs.append('Warning: High pressure threshold exceeded')
    return {'validation_passed': True, 'error_logs': logs}

def route_by_validation(state: CompressorState):
    return 'validate' if not state.get('validation_passed') else END

graph = StateGraph(CompressorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()