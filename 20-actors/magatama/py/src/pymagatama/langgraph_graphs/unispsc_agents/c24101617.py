from typing import TypedDict
from langgraph.graph import StateGraph, END

class LiftState(TypedDict):
    specs: dict
    approved: bool
    safety_check: bool

def validate_capacity(state: LiftState):
    capacity = state['specs'].get('load_kg', 0)
    return {'safety_check': capacity > 0 and capacity < 5000}

def approve_procurement(state: LiftState):
    return {'approved': state['safety_check'] == True}

graph = StateGraph(LiftState)
graph.add_node('validate', validate_capacity)
graph.add_node('approve', approve_procurement)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
