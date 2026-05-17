from typing import TypedDict
from langgraph.graph import StateGraph, END

class PinionState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: PinionState):
    required = ['module', 'teeth', 'hardness']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid, 'error': None if valid else 'Missing core specs'}

def structural_analysis(state: PinionState):
    if state['validated']:
        print('Performing gear tooth stress analysis...')
    return state

graph = StateGraph(PinionState)
graph.add_node('validate', validate_specs)
graph.add_node('analysis', structural_analysis)
graph.set_entry_point('validate')
graph.add_edge('validate', 'analysis')
graph.add_edge('analysis', END)
graph = graph.compile()