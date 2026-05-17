from typing import TypedDict
from langgraph.graph import StateGraph, END

class PostBoosterState(TypedDict):
    spec_data: dict
    validated: bool
    error: str

def validate_specs(state: PostBoosterState):
    required = ['Operating Pressure Range', 'Material Certification']
    missing = [f for f in required if f not in state['spec_data']]
    return {'validated': len(missing) == 0, 'error': f'Missing: {missing}' if missing else ''}

def route_by_validation(state: PostBoosterState):
    return 'valid' if state['validated'] else 'invalid'

graph = StateGraph(PostBoosterState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()