from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: CastingState):
    required = ['Material Grade', 'Dimensional Tolerance']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed, 'error_log': [] if passed else ['Missing specifications']}

def route_by_validation(state: CastingState):
    return 'process' if state['validation_passed'] else END

def process_casting(state: CastingState):
    print('Proceeding with metallurgical analysis and CAD verification...')
    return {'error_log': ['Analysis complete']}

graph = StateGraph(CastingState)
graph.add_node('validator', validate_specs)
graph.add_node('process', process_casting)
graph.set_entry_point('validator')
graph.add_conditional_edges('validator', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()
