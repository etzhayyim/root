from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChairState(TypedDict):
    specifications: dict
    validation_passed: bool

def validate_specs(state: ChairState):
    required = ['material', 'weight_capacity']
    passed = all(k in state['specifications'] for k in required)
    return {'validation_passed': passed}

def route_by_validation(state: ChairState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(ChairState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()