from typing import TypedDict
from langgraph.graph import StateGraph, END

class DuplicatorState(TypedDict):
    specs: dict
    validation_flag: bool

def validate_specs(state: DuplicatorState):
    required = ['speed', 'resolution']
    state['validation_flag'] = all(k in state['specs'] for k in required)
    return state

def check_compliance(state: DuplicatorState):
    return 'valid' if state['validation_flag'] else 'invalid'

graph = StateGraph(DuplicatorState)
graph.add_node('validator', validate_specs)
graph.add_edge('validator', END)
graph.set_entry_point('validator')
graph = graph.compile()
