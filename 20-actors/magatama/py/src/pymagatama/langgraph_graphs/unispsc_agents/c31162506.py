from typing import TypedDict
from langgraph.graph import StateGraph, END

class BracketState(TypedDict):
    load_capacity: float
    material: str
    is_compliant: bool

def validate_load_capacity(state: BracketState):
    state['is_compliant'] = state['load_capacity'] > 0
    return state

def check_material(state: BracketState):
    if state['material'] not in ['Steel', 'Aluminum', 'Plastic']:
        state['is_compliant'] = False
    return state

graph = StateGraph(BracketState)
graph.add_node('validate_load', validate_load_capacity)
graph.add_node('check_mat', check_material)
graph.set_entry_point('validate_load')
graph.add_edge('validate_load', 'check_mat')
graph.add_edge('check_mat', END)
graph = graph.compile()