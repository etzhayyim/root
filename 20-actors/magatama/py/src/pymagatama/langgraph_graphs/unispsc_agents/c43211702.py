from typing import TypedDict
from langgraph.graph import StateGraph, END

class ReaderState(TypedDict):
    device_id: str
    spec_data: dict
    validated: bool

def validate_specs(state: ReaderState):
    required = ['magnetic_encoding_standard', 'interface_type']
    state['validated'] = all(k in state['spec_data'] for k in required)
    return state

def process_encoder(state: ReaderState):
    return {'validated': state['validated']}

graph = StateGraph(ReaderState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_encoder)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()