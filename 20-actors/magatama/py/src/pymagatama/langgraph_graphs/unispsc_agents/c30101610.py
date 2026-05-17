from typing import TypedDict
from langgraph.graph import StateGraph, END

class BrassBarState(TypedDict):
    spec: dict
    validated: bool
    error: str

def validate_specs(state: BrassBarState):
    required = ['grade', 'diameter', 'length']
    if all(k in state['spec'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required specs'}

def process_order(state: BrassBarState):
    if state['validated']:
        print('Brass bar specification validated for procurement.')
    return state

graph = StateGraph(BrassBarState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_order)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()