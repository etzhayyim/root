from typing import TypedDict
from langgraph.graph import StateGraph, END

class CarrierState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: CarrierState):
    required = ['tolerance', 'hardness']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid, 'error': '' if valid else 'Missing specs'}

def process_carrier(state: CarrierState):
    print('Processing planet carrier geometry...')
    return {'validated': True}

graph = StateGraph(CarrierState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_carrier)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)

compiled_graph = graph.compile()
