from typing import TypedDict
from langgraph.graph import StateGraph, END

class PusherHeadState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: PusherHeadState):
    required = ['material', 'tolerance', 'hardness']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed, 'error_log': [] if passed else ['Missing technical specs']}

def route_by_validation(state: PusherHeadState):
    return 'process' if state['validation_passed'] else 'end'

graph = StateGraph(PusherHeadState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': 'process', 'end': END})
graph.add_edge('process', END)
graph = graph.compile()