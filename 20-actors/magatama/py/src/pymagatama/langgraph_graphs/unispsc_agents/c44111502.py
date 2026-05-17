from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    specs: dict
    is_valid: bool

def validate_specs(state: State):
    required = ['dimensions', 'material']
    return {'is_valid': all(k in state['specs'] for k in required)}

def process_procurement(state: State):
    print('Processing desk organizer order...')
    return state

graph = StateGraph(State)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')