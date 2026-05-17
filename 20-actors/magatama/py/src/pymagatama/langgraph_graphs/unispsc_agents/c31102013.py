from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: CastingState):
    required = ['alloy_type', 'tensile_strength']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed, 'error_log': [] if passed else ['Missing critical specs']}

def process_casting(state: CastingState):
    return {'error_log': state['error_log'] + ['Processing zinc centrifugal casting protocol']}

graph = StateGraph(CastingState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_casting)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()