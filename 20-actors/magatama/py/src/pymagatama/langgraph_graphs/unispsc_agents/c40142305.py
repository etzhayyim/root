from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeReducerState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: PipeReducerState):
    required = ['material', 'pressure_rating', 'size']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def route_by_validation(state: PipeReducerState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(PipeReducerState)
graph.add_node('validate', validate_specs)
graph.add_edge('__start__', 'validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': END, '__end__': END})
graph.set_entry_point('validate')
compiled_graph = graph.compile()