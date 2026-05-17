from typing import TypedDict
from langgraph.graph import StateGraph, END

class MortarState(TypedDict):
    spec_data: dict
    approved: bool

def validate_mortar_specs(state: MortarState):
    strength = state['spec_data'].get('compressive_strength', 0)
    state['approved'] = strength >= 15.0
    return state

def check_shelf_life(state: MortarState):
    state['approved'] = state['approved'] and state['spec_data'].get('shelf_life', 0) > 3
    return state

graph = StateGraph(MortarState)
graph.add_node('validate', validate_mortar_specs)
graph.add_node('expiry', check_shelf_life)
graph.set_entry_point('validate')
graph.add_edge('validate', 'expiry')
graph.add_edge('expiry', END)
graph = graph.compile()