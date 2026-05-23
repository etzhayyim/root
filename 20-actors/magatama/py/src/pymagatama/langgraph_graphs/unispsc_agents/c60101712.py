from typing import TypedDict
from langgraph.graph import StateGraph, END

class HallPassState(TypedDict):
    quantity: int
    material_type: str
    is_approved: bool

def validate_request(state: HallPassState):
    state['is_approved'] = state['quantity'] > 0 and state['material_type'] in ['plastic', 'cardstock']
    return state

def route_by_approval(state: HallPassState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(HallPassState)
graph.add_node('validate', validate_request)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
# Implementation logic compiled into the StateGraph
