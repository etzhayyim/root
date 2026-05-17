from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    spec_data: dict
    validated: bool
    error: str

def validate_specs(state: ProcessingState):
    required = ['precision_tolerance', 'interface_compatibility']
    state['validated'] = all(k in state['spec_data'] for k in required)
    return state

def route_logic(state: ProcessingState):
    return 'process' if state['validated'] else 'reject'

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()