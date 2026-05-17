from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoilTapeState(TypedDict):
    spec: dict
    validated: bool
    error: str

def validate_tape_specs(state: FoilTapeState):
    required = ['heat_resistance', 'adhesive_type', 'width']
    if all(k in state['spec'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required specs'}

def process_procurement(state: FoilTapeState):
    if state['validated']:
        print('Proceeding to quote generation')
    return state

graph = StateGraph(FoilTapeState)
graph.add_node('validate', validate_tape_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')