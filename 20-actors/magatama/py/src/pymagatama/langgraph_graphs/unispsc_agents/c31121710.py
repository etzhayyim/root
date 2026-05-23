from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    spec_data: dict
    validated: bool
    error: str

def validate_specs(state: CastingState):
    required = ['Material Composition', 'Dimensional Tolerance']
    valid = all(k in state['spec_data'] for k in required)
    return {'validated': valid, 'error': '' if valid else 'Missing required spec fields'}

def process_casting(state: CastingState):
    if state['validated']:
        print('Processing centrifugal copper casting analysis...')
    return state

graph = StateGraph(CastingState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_casting)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()
