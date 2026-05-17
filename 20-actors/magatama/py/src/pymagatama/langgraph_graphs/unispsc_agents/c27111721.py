from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CrankState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_crank_specs(state: CrankState):
    required = ['Material Grade', 'Tensile Strength']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing core specs'}

def process_crank(state: CrankState):
    print('Processing crank validation workflow')
    return state

graph = StateGraph(CrankState)
graph.add_node('validate', validate_crank_specs)
graph.add_node('process', process_crank)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()