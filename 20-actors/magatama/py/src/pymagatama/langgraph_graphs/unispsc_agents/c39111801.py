from typing import TypedDict
from langgraph.graph import StateGraph, END

class BallastState(TypedDict):
    specs: dict
    validated: bool

def validate_specs(state: BallastState):
    required = ['voltage', 'frequency', 'certification']
    all_present = all(k in state['specs'] for k in required)
    return {'validated': all_present}

def route_by_validation(state: BallastState):
    return 'valid' if state['validated'] else 'invalid'

graph = StateGraph(BallastState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
