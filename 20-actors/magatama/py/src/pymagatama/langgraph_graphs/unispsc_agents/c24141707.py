from typing import TypedDict
from langgraph.graph import StateGraph, END

class ReelState(TypedDict):
    spec: dict
    validated: bool

def validate_reel_specs(state: ReelState):
    required = ['load_capacity', 'material']
    return {'validated': all(k in state['spec'] for k in required)}

def route_by_spec(state: ReelState):
    return 'valid' if state['validated'] else 'reject'

graph = StateGraph(ReelState)
graph.add_node('validate', validate_reel_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')