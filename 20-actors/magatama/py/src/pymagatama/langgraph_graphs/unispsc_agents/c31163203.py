from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PinState(TypedDict):
    material: str
    tolerance: float
    compliant: bool

def validate_tolerance(state: PinState):
    state['compliant'] = state['tolerance'] <= 0.01
    return state

def check_material(state: PinState):
    state['compliant'] = state['compliant'] and (state['material'] in ['stainless_steel', 'carbon_steel'])
    return state

graph = StateGraph(PinState)
graph.add_node('validate_tol', validate_tolerance)
graph.add_node('check_mat', check_material)
graph.set_entry_point('validate_tol')
graph.add_edge('validate_tol', 'check_mat')
graph.add_edge('check_mat', END)
graph = graph.compile()