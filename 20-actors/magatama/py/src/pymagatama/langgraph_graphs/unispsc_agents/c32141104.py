from typing import TypedDict
from langgraph.graph import StateGraph, END

class DeflectionState(TypedDict):
    spec_data: dict
    validated: bool
    error: str

def validate_specs(state: DeflectionState):
    required = ['frequency_range', 'material_composition']
    valid = all(k in state['spec_data'] for k in required)
    return {'validated': valid, 'error': '' if valid else 'Missing required fields'}

def route(state: DeflectionState):
    return 'process' if state['validated'] else END

graph = StateGraph(DeflectionState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route)
graph.add_edge('process', END)
graph = graph.compile()
