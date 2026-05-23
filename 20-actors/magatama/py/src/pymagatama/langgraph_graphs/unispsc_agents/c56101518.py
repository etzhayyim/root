from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RackState(TypedDict):
    load_weight: float
    specs_verified: bool
    safety_check: str

def validate_load_capacity(state: RackState):
    state['specs_verified'] = state['load_weight'] <= 500
    return state

def perform_safety_check(state: RackState):
    state['safety_check'] = 'PASS' if state['specs_verified'] else 'FAIL'
    return state

graph = StateGraph(RackState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('safety', perform_safety_check)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
