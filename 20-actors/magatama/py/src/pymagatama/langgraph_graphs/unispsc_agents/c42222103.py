from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_load_capacity(state: State):
    capacity = state['spec_data'].get('load_kg', 0)
    state['is_compliant'] = capacity >= 2.0
    return state

def check_certification(state: State):
    certs = state['spec_data'].get('certifications', [])
    state['is_compliant'] = state['is_compliant'] and 'ISO13485' in certs
    return state

graph = StateGraph(State)
graph.add_node('validate_load', validate_load_capacity)
graph.add_node('validate_cert', check_certification)
graph.add_edge('validate_load', 'validate_cert')
graph.add_edge('validate_cert', END)
graph.set_entry_point('validate_load')
graph = graph.compile()