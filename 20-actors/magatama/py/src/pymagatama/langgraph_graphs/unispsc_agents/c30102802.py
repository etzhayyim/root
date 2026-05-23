from typing import TypedDict
from langgraph.graph import StateGraph, END

class ConcreteState(TypedDict):
    load_capacity: float
    specs_verified: bool

def validate_load(state: ConcreteState) -> ConcreteState:
    state['specs_verified'] = state['load_capacity'] > 500
    return state

def check_certification(state: ConcreteState) -> ConcreteState:
    return state

graph = StateGraph(ConcreteState)
graph.add_node('validate', validate_load)
graph.add_node('certify', check_certification)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph = graph.compile()
