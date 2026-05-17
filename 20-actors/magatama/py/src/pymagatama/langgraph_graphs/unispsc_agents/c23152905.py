from typing import TypedDict
from langgraph.graph import StateGraph, END

class FastenerState(TypedDict):
    spec_data: dict
    validation_status: str

def validate_spec(state: FastenerState):
    required = ['material', 'size', 'standard']
    valid = all(k in state['spec_data'] for k in required)
    return {'validation_status': 'passed' if valid else 'failed'}

def route_by_validation(state: FastenerState):
    return 'process' if state['validation_status'] == 'passed' else END

graph = StateGraph(FastenerState)
graph.add_node('validate', validate_spec)
graph.add_node('process', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': 'process'})
graph.add_edge('process', END)
graph = graph.compile()